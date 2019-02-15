const m = require('mithril')
const jstz = require('jstimezonedetect')

class IssuesModel {
  constructor() {
    this.issues = {}
    this.timezone = jstz.determine().name()
  }
  async loadIssues() {
    let response = await m.request({method: 'GET', url: '/issues', data: {tz: this.timezone}})
    this.issues = {}
    for (let issue of response.issues) {
      this.issues[issue.id] = issue
    }
    return this.issues
  }
  get list() {
    return Object.keys(this.issues).map(i => this.issues[i])
  }
  async loadIssue(issueId) {
    let response = await m.request({method: 'GET', url: `/issues/${issueId}`, data: {tz: this.timezone}})
    if ('error' in response) {
      return null
    }
    this.issues[issueId] = response
    return response
  }
  async updateIssue(issueId, fields) {
    await m.request({
      method: "PUT",
      url: `/issues/${issueId}`,
      data: fields
    })
    return await this.loadIssue(issueId)
  }
  async createIssue(fields) {
    await m.request({
      method: "POST",
      url: `/issues`,
      data: fields
    })
    return await this.loadIssues()
  }
}

module.exports = {IssuesModel}
