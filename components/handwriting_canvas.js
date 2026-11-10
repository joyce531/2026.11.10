export default function(component) {
  const {parentElement: root, data, setTriggerValue} = component;
  const canvas = root.querySelector('canvas');
  const context = canvas.getContext('2d');
  const brush = root.querySelector('.brush'), color = root.querySelector('.color');
  const undo = root.querySelector('.undo'), clear = root.querySelector('.clear');
  const submit = root.querySelector('.submit'), status = root.querySelector('.status');
  const state = canvas.naxiState || (canvas.naxiState = {strokes: [], current: null});
  function render() {
    context.fillStyle = 'white'; context.fillRect(0, 0, 640, 480);
    for (const stroke of [...state.strokes, ...(state.current ? [state.current] : [])]) {
      context.strokeStyle = stroke.color; context.fillStyle = stroke.color;
      context.lineWidth = stroke.width; context.lineJoin = 'round'; context.lineCap = 'round';
      const points = stroke.points;
      context.beginPath(); context.arc(points[0][0], points[0][1], stroke.width/2, 0, Math.PI*2); context.fill();
      context.beginPath(); context.moveTo(...points[0]);
      points.slice(1).forEach(p => context.lineTo(...p)); context.stroke();
    }
    undo.disabled = state.strokes.length === 0;
  }
  function point(e) {
    const r = canvas.getBoundingClientRect();
    return [Math.max(0, Math.min(640, (e.clientX-r.left)*640/r.width)), Math.max(0, Math.min(480, (e.clientY-r.top)*480/r.height))];
  }
  canvas.onpointerdown = e => {
    if (e.button !== 0 || state.current) return;
    if (state.strokes.length >= 300) {status.textContent='已达到 300 笔上限，请清空后再试。'; return;}
    canvas.setPointerCapture(e.pointerId);
    state.current = {width:Number(brush.value), color:color.value, points:[point(e)]};
    status.textContent = '书写已修改，请提交以评价当前画布。'; render();
  };
  canvas.onpointermove = e => {
    if (!state.current) return;
    if (state.current.points.length < 5000) state.current.points.push(point(e));
    render();
  };
  function finish(e) {
    if (!state.current) return;
    state.strokes.push(state.current); state.current = null;
    if (canvas.hasPointerCapture(e.pointerId)) canvas.releasePointerCapture(e.pointerId);
    render();
  }
  canvas.onpointerup = finish; canvas.onpointercancel = finish;
  brush.oninput = () => {root.querySelector('.size').textContent = brush.value;};
  undo.onclick = () => {state.strokes.pop(); state.current=null; render(); status.textContent='已撤销，请重新提交评价。';};
  clear.onclick = () => {state.strokes=[]; state.current=null; render(); status.textContent='画布已清空。下方如有结果，是上次提交的快照。';};
  submit.disabled = !data.enabled;
  submit.onclick = () => {
    if (state.current) return;
    setTriggerValue('submission', {png: canvas.toDataURL('image/png'),
      strokes: state.strokes, width:640, height:480, version:1,
      submission_id: crypto.randomUUID()});
    status.textContent = '已提交当前画布，请查看下方评价结果。';
  };
  render();
  return () => {
    canvas.onpointerdown=canvas.onpointermove=canvas.onpointerup=canvas.onpointercancel=null;
    brush.oninput=undo.onclick=clear.onclick=submit.onclick=null;
  };
}
