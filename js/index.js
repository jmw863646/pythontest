require('babel-polyfill')
const m = require('mithril')
const {IssuesList, ViewIssue, CreateIssue, EditIssue, RegisterUser, LoginUser, Dashboard, ToolbarContainer} = require('./views')

m.route(document.body, '/issues', {
  '/issues': {
    render(vnode) {
      return m(ToolbarContainer, m(IssuesList))
    }
  },
  '/issues/create': {
    render(vnode) {
      return m(ToolbarContainer, m(CreateIssue))
    }
  },
  '/issues/:issueId': {
    render(vnode) {
      return m(
        ToolbarContainer,
        (vnode.attrs.issueId === 'new')
        ? m(CreateIssue)
        : m(ViewIssue, {issueId: vnode.attrs.issueId}))
    }
  },
  '/issues/:issueId/edit': {
    render(vnode) {
      return m(ToolbarContainer, m(EditIssue, {issueId: vnode.attrs.issueId}))
    }
  },
  '/dashboard': {
    render(vnode) {
      return m(ToolbarContainer, m(Dashboard))
    }
  },
  '/register': {
    render(vnode) {
      return m(ToolbarContainer, m(RegisterUser))
    }
  },
  '/login': {
    render(vnode) {
      return m(ToolbarContainer, m(LoginUser))
    }
  }
})
