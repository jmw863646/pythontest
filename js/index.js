require('babel-polyfill')
const m = require('mithril')
const {IssuesList, ViewIssue, CreateIssue, EditIssue, ToolbarContainer} = require('./views')
const {IssuesModel} = require('./viewmodels')

const issuesModel = new IssuesModel()

m.route(document.body, '/issues', {
  '/issues': {
    render(vnode) {
      return m(ToolbarContainer, m(IssuesList, {model: issuesModel}))
    }
  },
  '/issues/create': {
    render(vnode) {
      return m(ToolbarContainer, m(CreateIssue, {model: issuesModel}))
    }
  },
  '/issues/:issueId': {
    render(vnode) {
      return m(
        ToolbarContainer,
        (vnode.attrs.issueId === 'new')
        ? m(CreateIssue, {model: issuesModel})
        : m(ViewIssue, {model: issuesModel, issueId: vnode.attrs.issueId}))
    }
  },
  '/issues/:issueId/edit': {
    render(vnode) {
      return m(ToolbarContainer, m(EditIssue, {model: issuesModel, issueId: vnode.attrs.issueId}))
    }
  }
})
