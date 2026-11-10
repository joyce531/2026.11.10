"""OpenCV preprocessing and conservative printed-score routing; originals stay untouched."""
from functools import lru_cache
from io import BytesIO
from pathlib import Path
import warnings

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from tools.upload_validation import prepare_image, validate_size


def load_score_image(data, filename):
    validate_size(data,10)
    if Path(filename).suffix.lower()=='.webp':
        try:
            with warnings.catch_warnings():
                warnings.simplefilter('error',Image.DecompressionBombWarning)
                with Image.open(BytesIO(data)) as im:
                    if im.format!='WEBP' or im.width*im.height>16000000:
                        raise ValueError('WEBP 格式或像素限制无效。')
                    if getattr(im,'n_frames',1)>1:raise ValueError('不支持动画曲谱。')
                    im.load();out=BytesIO();im.convert('RGB').save(out,format='PNG')
            return prepare_image(out.getvalue(),'score.png')[0]
        except (OSError,Image.DecompressionBombWarning,Image.DecompressionBombError):
            raise ValueError('WEBP 图片无法安全读取。') from None
    return prepare_image(data,filename)[0]


def _normal_glyph(x):
    ys,xs=np.where(x>0)
    if not len(xs):return np.zeros((32,24),dtype=np.uint8)
    crop=x[ys.min():ys.max()+1,xs.min():xs.max()+1]
    scale=min(20/crop.shape[1],28/crop.shape[0])
    small=cv2.resize(crop,(max(1,round(crop.shape[1]*scale)),max(1,round(crop.shape[0]*scale))))
    out=np.zeros((32,24),dtype=np.uint8);y=(32-small.shape[0])//2;z=(24-small.shape[1])//2
    out[y:y+small.shape[0],z:z+small.shape[1]]=small
    return out


@lru_cache(maxsize=1)
def _digit_templates():
    templates=[]
    for name in ('arial.ttf','arialbd.ttf','times.ttf','timesbd.ttf'):
        path=Path('C:/Windows/Fonts')/name
        if not path.exists():continue
        font=ImageFont.truetype(str(path),40)
        for digit in '01234567':
            canvas=Image.new('L',(60,60));ImageDraw.Draw(canvas).text((6,2),digit,font=font,fill=255)
            templates.append(_normal_glyph(np.asarray(canvas)))
    return templates


def preprocess(image):
    rgb=np.asarray(image.convert('RGB'))
    if min(rgb.shape[:2])<60:raise ValueError('曲谱图片过小，请上传更清晰的印刷谱。')
    scale=min(2.,2000/rgb.shape[1])
    if scale>1:rgb=cv2.resize(rgb,None,fx=scale,fy=scale,interpolation=cv2.INTER_CUBIC)
    gray=cv2.cvtColor(rgb,cv2.COLOR_RGB2GRAY)
    # Do not erode or remove dots/underlines: these are musical information.
    background=cv2.GaussianBlur(gray,(0,0),25)
    gray=cv2.divide(gray,np.maximum(background,1),scale=255)
    ink=cv2.adaptiveThreshold(gray,255,cv2.ADAPTIVE_THRESH_GAUSSIAN_C,cv2.THRESH_BINARY_INV,35,13)
    lines=cv2.HoughLinesP(ink,1,np.pi/1800,threshold=60,minLineLength=gray.shape[1]//8,maxLineGap=15)
    angles=[]
    if lines is not None:
        for x1,y1,x2,y2 in lines.reshape(-1,4):
            angle=np.degrees(np.arctan2(y2-y1,x2-x1))
            if abs(angle)<7:angles.append(angle)
    angle=float(np.median(angles)) if angles else 0.
    if .15<abs(angle)<7:
        matrix=cv2.getRotationMatrix2D((gray.shape[1]/2,gray.shape[0]/2),angle,1)
        gray=cv2.warpAffine(gray,matrix,(gray.shape[1],gray.shape[0]),borderValue=255)
        ink=cv2.adaptiveThreshold(gray,255,cv2.ADAPTIVE_THRESH_GAUSSIAN_C,cv2.THRESH_BINARY_INV,35,13)
    if np.count_nonzero(ink)<50:raise ValueError('未检测到可读曲谱内容。')
    return Image.fromarray(gray).convert('RGB'),ink,{'deskew_degrees':round(angle,3),'size':list(gray.shape[::-1])}


def classify(ink):
    h,w=ink.shape
    horizontal=cv2.morphologyEx(ink,cv2.MORPH_OPEN,np.ones((1,max(30,w//10)),np.uint8))
    projections=(horizontal>0).sum(axis=1)
    ys=np.where(projections>w*.22)[0]
    bands=[]
    for y in ys:
        if not bands or y-bands[-1][-1]>2:bands.append([int(y)])
        else:bands[-1].append(int(y))
    centers=[float(np.mean(b)) for b in bands]
    groups=[];i=0
    while i+4<len(centers):
        gaps=np.diff(centers[i:i+5])
        if 3<=gaps.mean()<=h*.05 and gaps.std()<max(1.2,gaps.mean()*.16):
            groups.append(centers[i:i+5]);i+=5
        else:i+=1
    # Positive digit-shape evidence is required; "no staff" is never sufficient.
    count,labels,stats,_=cv2.connectedComponentsWithStats(ink)
    digit_boxes=[];templates=_digit_templates()
    for index in range(1,count):
        x,y,cw,ch,area=stats[index]
        if not (8<=ch<=h*.06 and .15<=cw/ch<=1.3 and area>=15):continue
        glyph=_normal_glyph(np.where(labels[y:y+ch,x:x+cw]==index,255,0).astype('uint8'))
        score=max((float(cv2.matchTemplate(glyph,t,cv2.TM_CCOEFF_NORMED)[0,0]) for t in templates),default=0)
        if score>.72:digit_boxes.append((int(x),int(y),int(cw),int(ch)))
    rows=[]
    for box in sorted(digit_boxes,key=lambda b:b[1]):
        cy=box[1]+box[3]/2
        if not rows or abs(cy-np.mean([b[1]+b[3]/2 for b in rows[-1]]))>box[3]*.6:rows.append([box])
        else:rows[-1].append(box)
    digit_count=sum(len(row) for row in rows if len(row)>=4)
    # Staff takes precedence; large separated numeral regions alongside staff are ambiguous.
    if groups:
        outside=[b for row in rows if len(row)>=8 for b in row
                 if not any(g[0]-3*(g[1]-g[0])<=b[1]<=g[-1]+3*(g[1]-g[0]) for g in groups)]
        kind='unknown' if len(outside)>max(24,len(groups)*12) else 'staff'
    else:kind='jianpu' if digit_count>=8 else 'unknown'
    return {'kind':kind,'staff_groups':len(groups),'digit_candidates':digit_count,
            'reason':'五线等距线组与数字形状规则判别，非识谱准确率；混排或证据不足时需人工选择。'}
