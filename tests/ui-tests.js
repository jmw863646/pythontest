global.window = require("mithril/test-utils/browserMock.js")();
global.document = window.document;
const $defineRoutes = global.window.$defineRoutes

const m = require('mithril')
const o = require('mithril/ospec/ospec')
const mq = require('mithril-query')

const {IssuesList, IssueEditor} = require('../js/views.js')
const {IssuesModel} = require('../js/viewmodels.js')

class FakeIssuesModel {
  constructor(issues = {}) {
    this.issues = issues
    this.issuesLoaded = {}
  }
  async loadIssues() {
    this.issuesLoaded.all = true
    return this.issues
  }
  get list() {
    return Object.keys(this.issues).map(i => this.issues[i])
  }
  async loadIssue(issueId) {
    this.issuesLoaded[issueId] = true
    return this.issues[issueId]
  }
  async updateIssue(issueId, fields) {
    for (let field in fields) {
      this.issues[issueId][field] = fields[field]
    }
    return this.issues[issueId]
  }
  async createIssue(fields) {
    this.issues.newest = fields
  }
}

o.spec('Bug Tracker UI', function() {
  o.spec('IssuesList', function() {
    let fakeModel
    o.before(function() {
      fakeModel = new FakeIssuesModel([{
        id: 1,
        title: 'Test Issue',
        opened: '2018-01-01T12:00:00.000',
        closed: '2018-01-01T13:00:00.000'
      }])
    })

    o('should display issues', function() {
      let output = mq(m(
        IssuesList, {
          model: fakeModel
        }
      ))

      output.should.have(1, 'table tr')
      let row = output.find('table tr')[0]
      mq(row, 'td.title-cell').should.contain('Test Issue')
      mq(row, 'td.title-cell').should.have('a[href="/issues/1"]')
      mq(row, 'td.opened-cell').should.contain('2018-01-01T12:00:00.000')
      mq(row, 'td.closed-cell').should.contain('2018-01-01T13:00:00.000')
      o(fakeModel.issuesLoaded.all).equals(true)
    })
  })

  o.spec('IssueEditor', function() {
    o('should edit issues', function() {
      let submitSpy = o.spy()
      let output = mq(m(
        IssueEditor, {
          title: 'Issue Title',
          descriptionText: 'Issue Description',
          onSubmit: submitSpy
        }
      ))
      output.setValue('#title-input', 'Updated Title')
      output.setValue('#description-input', 'Updated Description')
      output.trigger('form', 'onsubmit')
      let updated = submitSpy.args[0]
      o(updated.title).equals('Updated Title')
      o(updated.descriptionText).equals('Updated Description')
    })
  })

  o.spec('IssuesModel', function() {
    o('should load issues', async function() {
      $defineRoutes({ // Configure mock routes
        'GET /issues': function() {return {
          status: 200,
          responseText: `{
            "issues": [
              {
                "id": 1,
                "title": "Test Issue",
                "opened": "2018-01-01T12:00:00.000",
                "closed": "2018-01-01T13:00:00.000",
                "description": "An example issue"
              }
            ]
          }`
        }}
      })
      let instance = new IssuesModel()
      let issues = await instance.loadIssues()
      o(issues).deepEquals({
        1: {
          id: 1,
          title: 'Test Issue',
          opened: '2018-01-01T12:00:00.000',
          closed: '2018-01-01T13:00:00.000',
          description: 'An example issue'
        }
      })
      o(instance.list).deepEquals([
        {
          id: 1,
          title: 'Test Issue',
          opened: '2018-01-01T12:00:00.000',
          closed: '2018-01-01T13:00:00.000',
          description: 'An example issue'
        }
      ])
    })
    o('should update issues', async function() {
      $defineRoutes({ // Configure mock routes
        'PUT /issues/1': function(req) {
          o(JSON.parse(req.body).descriptionText).equals('Updated Text')
          return {
            status: 204,
            responseText: ''
          }
        },
        'GET /issues/1': function() {return {
          status: 204,
          responseText: `{
            "id": 1,
            "title": "Test Issue",
            "opened": "2018-01-01T12:00:00.000",
            "closed": "2018-01-01T13:00:00.000",
            "description": "Updated Text"
          }`
        }}
      })
      let instance = new IssuesModel()
      let updated = await instance.updateIssue(1, {descriptionText: "Updated Text"})
      o(updated.description).equals("Updated Text")
    })
  })
})
