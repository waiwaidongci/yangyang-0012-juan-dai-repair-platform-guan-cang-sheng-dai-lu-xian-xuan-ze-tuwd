import {api, h, notice} from '/base.js'

export const option = (value, label, selected = false) =>
  '<option value="' + h(value) + '"' + (selected ? ' selected' : '') + '>' + h(label) + '</option>'

export function wireForms(outlet, refresh, actions) {
  for (const form of outlet.querySelectorAll('form[data-operation]')) {
    form.addEventListener('submit', async event => {
      event.preventDefault()
      const button = form.querySelector('button[type=submit], button:not([type])')
      const status = form.querySelector('[role=status]')
      button.disabled = true
      try {
        const values = Object.fromEntries(new FormData(form))
        const command = actions[form.dataset.operation](values, form)
        await api(command.path, command.method ?? 'POST', command.body ?? values)
        await refresh('已保存。')
      } catch (error) {
        notice(status, error.message, true)
      } finally {
        button.disabled = false
      }
    })
  }
}

export const message = text => text
  ? '<p role="status" data-type="success">' + h(text) + '</p>'
  : ''
