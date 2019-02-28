const m = require('mithril')
const {IssuesModelSingleton,UserModelSingleton} = require('./viewmodels')


class IssuesList {
  constructor(vnode) {
  }
  oninit() {
    IssuesModelSingleton.loadIssues()
  }
  view() {
    return m('table.table', [
      m('thead', [
        m('th', 'title'),
        m('th', 'opened'),
        m('th', 'closed')
      ]),
      m('tbody', [
        IssuesModelSingleton.list.map(item =>
          m('tr', [
            m('td.title-cell', m("a", {href: `/issues/${item.id}`, oncreate: m.route.link}, item.title)),
            m('td.opened-cell', item.opened),
            m('td.closed-cell', item.closed)
          ])
        )
      ])
    ])
  }
}

class ViewIssue {
  constructor(vnode) {
    this.issueId = vnode.attrs.issueId
  }
  oninit() {
    IssuesModelSingleton.loadIssue(this.issueId)
  }
  view() {
    let detail = IssuesModelSingleton.issues[this.issueId]
    if (detail) {
      var titleElements = [
        m('h1.col-sm-11', detail.title)
      ]

      // User is allowed to edit if they've logged in
      if (UserModelSingleton.email()) {
        titleElements.push(
          m('.col-sm-1',
            m(
              'a.btn.btn-primary',
              {href: `/issues/${this.issueId}/edit`, oncreate: m.route.link},
              'Edit'
            )
          )
        )
      }

      return m('div', [
        m('.row', titleElements),
        m('dl.row', [
          m('dt.col-sm-3', 'Opened'),
          m('dd.col-sm-3', detail.opened),
          m('dt.col-sm-3', 'Closed'),
          m('dd.col-sm-3', detail.closed),
        ]),
        m('h2', 'Description'),
        m('p.description', detail.description)
      ]
    )
    } else {
      return m('.alert.alert-info', 'Cannot find issue #' + this.issueId)
    }
  }
}

class EditIssue {
  constructor(vnode) {
    this.issueId = vnode.attrs.issueId
  }
  async oninit() {
    await IssuesModelSingleton.loadIssue(this.issueId)
  }
  view() {
    let issue = IssuesModelSingleton.issues[this.issueId]
    return issue
    ? m(IssueEditor, {
      title: issue.title,
      descriptionText: issue.description,
      closedFlag: Boolean(issue.closed),
      onSubmit: async (fields) => {
        // Server-side expects 'description' but client-side calls it 'descriptionText'
        renamedFields = {}
        for (k in fields) {
          if (k == 'descriptionText') {
            renamedFields['description'] = fields['descriptionText']
          } else {
            renamedFields[k] = fields[k]
          }
        }

        UserModelSingleton.addAuthentication(renamedFields)
        var status = await IssuesModelSingleton.updateIssue(this.issueId, renamedFields)
        m.route.set((status === false) ? '/login' : `/issues/${this.issueId}`)
        m.redraw()
      }
    })
    :m('.alert.alert-info', 'Loading')
  }
}

class CreateIssue {
  constructor(vnode) {
  }
  view() {
    return m(IssueEditor, {
      title: '',
      descriptionText: '',
      closedFlag: null,
      onSubmit: async ({descriptionText, title}) => {
        var status = await IssuesModelSingleton.createIssue({description: descriptionText, title: title})
        m.route.set((status === false) ? '/login' : '/issues')
        m.redraw()
      }
    })
  }
}

class IssueEditor {
  constructor(vnode) {
    this.title = vnode.attrs.title
    this.descriptionText = vnode.attrs.descriptionText
    this.closedFlag = vnode.attrs.closedFlag
    this.onSubmit = vnode.attrs.onSubmit
  }
  view() {
    groups = [
      m('.form-group', [
        m('label', {'for': 'title-input'}, 'Issue Title'),
        m('input.form-control#title-input', {value: this.title, oninput: (e) => {this.title = e.target.value}})
      ]),
      m('.form-group', [
        m('label', {'for': 'description-input'}, 'Description'),
        m('textarea.form-control#description-input', {oninput: (e) => {this.descriptionText = e.target.value}}, this.descriptionText)
      ])
    ]

    // Don't display closed flag on creation
    if (this.closedFlag != null) {
      groups.push(m('.form.group', [
        m('label', {'for': 'closed-input'}, 'Closed'),
        m('input.form-control#closed-input', {type: 'checkbox', checked: this.closedFlag, onclick: (e) => { this.closedFlag = e.target.checked}})
      ]))
    }

    groups.push(m('button.btn.btn-primary#save-button', {type: 'submit'}, 'Save'))

    return m('form', {onsubmit: e => {
      // Prevent the form from automatically reloading the page so that Mithril can redraw or route appropriately
      e.preventDefault();

      this.onSubmit({title: this.title, descriptionText: this.descriptionText, closedFlag: this.closedFlag});
    }}, groups)
  }
}

/**
 * Create the view the login or register view.
 * 
 * @param {string} purpose Whether this is a 'Login' or 'Register' view.
 * @param {Object} owner   The owning view class.
 * @returns {Object} view
 */
function _createRegisterLoginUserView(purpose, owner) {
  var description = (purpose == 'Login') ? 'Login to bug tracker.' : 'Register to be able to create / edit bugs.'

  var groups = []
  if (purpose == 'Login') {
    groups.push([
      m('.form-group', [
        'Login to bug tracker if you have an existing account or ', 
        m('a', {href: '/register', oncreate: m.route.link}, 'register'),
        ' for a new one.'
      ])
    ])
  } else {
    groups.push(
      m('.form-group', 'Register for a new account to be able to create and edit issues.')
    )
  }

  if (owner.previousError) {
    groups = [
      m('.form-group', [
        m('.alert.alert-info', owner.previousError)
      ])
    ]
  }

  // Going to give the buttons different ids just to make integration testing simpler
  var buttonId = purpose.toLowerCase() + '-button'

  groups.push([ 
    m('.form-group', [
      m('label', {'for': 'email-input'}, 'E-mail Address'),
      m('input.form-control#email-input', {oninput: (e) => {owner.email = e.target.value}})
    ]),
    m('.form-group', [
      m('label', {'for': 'password'}, 'Password'),
      m('input.form-control#password-input', {type: 'password', oninput: (e) => {owner.password = e.target.value}})
    ]),
    m('button.btn.btn-primary#' + buttonId, {type: 'submit'}, purpose)
  ])

  return m('form', {onsubmit: e => { 
    // Prevent the form from automatically reloading the page so that Mithril can redraw or route appropriately
    e.preventDefault(); 
    
    owner.onSubmit(owner); 
  }}, groups)
}

/**
 * A view to register a new user.
 * 
 */
class RegisterUser {
  constructor(vnode) {
    this.previousError = null
  }

  view() {
    return _createRegisterLoginUserView('Register', this)
  }

  async onSubmit(owner) {
    this.previousError = null
    var response = await UserModelSingleton.register({email: owner.email, password: owner.password})
    if ((response) && ('error' in response)) {
      this.previousError = response['error']
    } else {
      // Now they need to login
      m.route.set('/login')
    }
    m.redraw()
  }
}

/**
 * A view to login an existing user.
 * 
 */
class LoginUser {
  constructor(vnode) {
    this.previousError = null
  }

  view() {
    return _createRegisterLoginUserView('Login', this)
  }

  async onSubmit(owner) {
    this.previousError = null
    var success = await UserModelSingleton.login({email: owner.email, password: owner.password})
    if (success) {
      // For the moment we'll just return to the main page
      m.route.set('/')
    } else {
      this.previousError = 'Combination of e-mail address and password was not recognised'
      m.route.set('/login')
    }
    m.redraw()
  }
}

/**
 * The elements of the toolbar container depend on whether a user is logged in.
 * 
 */
const ToolbarContainer = {
  view(vnode) {
    var listItems = []

    // Is a user logged in?
    if (UserModelSingleton.email()) {
      listItems.push([
        m('li.nav-item', UserModelSingleton.email()),
        m('li.nav-item', [
          m('a.nav-link', {href: '/issues/create', oncreate: m.route.link}, 'Create')
        ]),
        m('button.btn#logout-button', {onclick: e => { UserModelSingleton.logout() }}, 'Logout')
      ])
    } else {
      listItems.push(
        m('li.nav-item', [
          m('a.nav-link#navbar-login-button', {href: '/login', oncreate: m.route.link}, 'Login')
        ])
      )
    }

    return m('div', [
      m('nav.navbar.navbar-expand-lg.navbar-light.bg-light', [
        m('a.navbar-brand', {href: '/issues', oncreate: m.route.link}, 'Bug Tracker'),
        m('.collapse.navbar-collapse', [
          m('ul.navbar-nav', listItems)
        ])
      ]),
      m('.container', vnode.children)
    ])
  }
}

module.exports = {IssuesList, ViewIssue, EditIssue, CreateIssue, IssueEditor, RegisterUser, LoginUser, ToolbarContainer}
