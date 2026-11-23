import {api} from '/base.js'
import {message,option,wireForms} from '/workflow-ui.js'
import {outgoing} from './manifest-view.js'

const endpoint='/api/archive-handoffs'
export async function render(outlet,user,flash='') {
  const {partners,grants,handoffs,derivatives}=await api(endpoint)
  if (!outlet.isConnected) return
  const grantOptions=copy=>grants.filter(row=>row.reel===copy?.reel).map(row=>option(row.id,row.instrument_ref)).join('')
  outlet.innerHTML=`${message(flash)}<h1>馆际交付清单</h1><p>以已通过质检的访问副本、馆际授权与接收档案室建立交付清单。</p>
    <div class="handoff-grid"><section><h2>出库与签收履历</h2>${outgoing(handoffs,user)}</section>
    <aside class="handoff-intake"><h2>准备副本清单</h2>${user.role==='operator'&&derivatives.length?`<form data-operation="prepare">
    <label>访问副本<select name="derivative">${derivatives.map(row=>option(row.id,row.filename)).join('')}</select></label>
    <label>该卷馆际授权<select name="grant_id" required>${grantOptions(derivatives[0])}</select></label>
    <label>接收档案室<select name="partner">${partners.filter(row=>row.supports_access_copy).map(row=>option(row.slug,row.name)).join('')}</select></label>
    <label>使用说明<input name="purpose" minlength="6" maxlength="180" required></label><button>建立待出库清单</button><p role="status"></p></form>`:'<p>录入员准备清单。复核员确认授权仍然有效后办理出库，合作方回执入库时核对封套摘要。</p>'}</aside></div>`
  const picker=outlet.querySelector('[name=derivative]')
  if (picker) picker.onchange=()=>{
    outlet.querySelector('[name=grant_id]').innerHTML=grantOptions(derivatives.find(row=>row.id===Number(picker.value))) ||
       '<option value="">该卷没有可用馆际授权</option>'
  }
  const update=(form,action)=>`${endpoint}/${form.dataset.id}/${action}`
  wireForms(outlet,next=>render(outlet,user,next),{
    prepare: ()=>({path:endpoint}),
    release: (_values,form)=>({path:update(form,'release'),body:{}}),
    receipt: (_values,form)=>({path:update(form,'receipt')}),
    withdraw: (_values,form)=>({path:update(form,'withdraw'),body:{}}),
  })
}
