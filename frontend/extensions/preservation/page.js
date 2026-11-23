import {api} from '/base.js'
import {message,option,wireForms} from '/workflow-ui.js'
import {kinds,results} from './quality-sheet.js'

const endpoint='/api/tape-preservation'
export async function render(outlet,user,flash='') {
  const {work,checks}=await api(endpoint)
  if (!outlet.isConnected) return
  const authorised=work.filter(row=>row.stage==='authorised')
  outlet.innerHTML=`${message(flash)}<h1>派生件入档质检</h1><p>把离线采集清单、实测文件指标与已签工序卡绑定。每次质检均保留结果。</p>
    <div class="audio-grid"><section><h2>入档检验簿</h2>${results(checks,user.role==='reviewer')}</section>
    <aside class="audio-intake"><h2>录入检测清单</h2>${user.role==='operator'&&authorised.length?`<form data-operation="add">
    <label>工序卡<select name="card">${authorised.map(row=>option(row.id,row.excerpt+' · '+row.target_seconds+' s / '+row.target_channels+' 声道')).join('')}</select></label>
    <label>入档用途<select name="kind">${Object.entries(kinds).map(([key,label])=>option(key,label)).join('')}</select></label>
    <label>数字文件名<input name="filename" placeholder="YT26_V2.wav" required></label>
    <div class="audio-settings"><label>时长秒数<input type="number" name="duration_seconds" step=".01" min=".01" required></label>
    <label>采样率<select name="sample_rate">${[44100,48000,96000,192000].map(n=>option(n,n)).join('')}</select></label>
    <label>声道<select name="channels"><option>1</option><option>2</option></select></label><label>削波帧<input type="number" min="0" name="clipped_frames" value="0" required></label></div>
    <label>预期校验值<input name="expected_digest" pattern="[a-f0-9]{64}" required></label><label>实测校验值<input name="measured_digest" pattern="[a-f0-9]{64}" required></label>
    <button>提交质检</button><p role="status"></p></form>`:'<p>具有采集规格的工序卡签发后，由录入员补录检测结果。质检的母版与访问副本采用各自采样率政策。</p>'}</aside></div>`
  wireForms(outlet,next=>render(outlet,user,next),{
    add: values=>({path:endpoint+'/derivatives',body:{...values,channels:Number(values.channels),sample_rate:Number(values.sample_rate)}}),
    verify: (_values,form)=>({path:`${endpoint}/derivatives/${form.dataset.id}/verify`,body:{}})
  })
}
