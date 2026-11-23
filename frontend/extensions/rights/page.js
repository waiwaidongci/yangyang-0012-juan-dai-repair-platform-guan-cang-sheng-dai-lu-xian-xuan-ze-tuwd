import {api} from '/base.js'
import {message,option,wireForms} from '/workflow-ui.js'
import {permitRows,scopes} from './permit-ledger.js'

const endpoint='/api/tape-rights'
export async function render(outlet,user,flash='') {
  const {reels,grants}=await api(endpoint)
  if (!outlet.isConnected) return
  outlet.innerHTML=`${message(flash)}<h1>授权用途与署名</h1><p>按馆藏卷查看纸本授权、使用范围、生效区间和撤回依据。</p>
    <div class="permit-spread"><section>${permitRows(reels,grants,user.role==='reviewer')}</section>
    <aside class="permit-desk"><h2>纸本授权登记</h2>${user.role==='operator'?`<form data-operation="create">
    <label>馆藏卷<select name="reel">${reels.map(row=>option(row.code,row.code+' · '+row.recording)).join('')}</select></label>
    <label>授权书编号<input name="instrument_ref" minlength="5" maxlength="30" required></label>
    <label>用途<select name="access_scope">${Object.entries(scopes).map(([key,label])=>option(key,label)).join('')}</select></label>
    <div class="permit-dates"><label>生效<input type="date" name="begins" required></label><label>截止<input type="date" name="expires" required></label></div>
    <label>署名文本<textarea name="credit_line" minlength="4" maxlength="220" required></textarea></label>
    <button>登记授权书</button><p role="status"></p></form>`:'<p>同卷同用途的授权日期应当互斥。复核后，馆际交付可引用有效授权。</p>'}</aside></div>`
  wireForms(outlet,next=>render(outlet,user,next),{
    create: ()=>({path:endpoint}),
    approve: (_values,form)=>({path:`${endpoint}/${form.dataset.id}/approve`,body:{}}),
    revoke: (_values,form)=>({path:`${endpoint}/${form.dataset.id}/revoke`}),
  })
}
