const m = require('mithril')
const jstz = require('jstimezonedetect')

/**
 * The user model responsible for registering, logging in and out.
 */
class UserModel {
  constructor() {
    this.cachedEmail = null
  }

  /**
   * Register a new user.
   * 
   * @param {Object} fields Containing properties 'email' and 'password'.
   */
  async register(fields) {
    return await m.request({
      method: "POST", 
      url: '/register',
      data: fields
    })
  }

  /**
   * Login as an existing user and create cookies for the user and session id.
   * 
   * @param {Object} fields Containing properties 'email' and 'password'.
   * @return Whether successful.
   */
  async login(fields) {
    var owner = this

    owner.cachedEmail = fields.email
    await m.request({
      method: "POST",
      url: '/login',
      data: fields
    }).then(function(sessionDetails) {
      // Set the cookies to expire in 24 hours. The server will stop accepting the session id long before that.
      owner.setCookies({
        email: fields.email, 
        userId: sessionDetails.userId, 
        sessionId: sessionDetails.sessionId
      }, 1)
    }).catch(function(error) {
      owner.cachedEmail = null
    })

    return this.cachedEmail != null
  }

  /**
   * Logout removing user id and session id cookies.
   */
  async logout() {
    emailAndIds = this.getCookies()

    await m.request({
      method: 'POST',
      url: '/logout',
      data: {'userId': emailAndIds.userId}
    })

    this.setCookies({email: '', userId: '', sessionId: ''}, -1)
    this.cachedEmail = null
    m.redraw()
  }

  /**
   * Add authentication fields to the request.
   * 
   * @param {Object} fields Add 'userId' and 'sessionId' to ensure request succeeds.
   * @return Whether request could be authenticated.
   */
  addAuthentication(fields) {
    var emailAndIds = this.getCookies()
    if (!emailAndIds) {
      this.cachedEmail = null
      return false
    }

    this.cachedEmail = emailAndIds.email
    fields['userId'] = emailAndIds.userId
    fields['sessionId'] = emailAndIds.sessionId
    return true
  }

  /**
   * Get the email address of the current user.
   * 
   * @return Email address or null if no one is logged in.
   * 
   */
  email() {
    if (!this.cachedEmail) {
      // Look in the cookies
      var emailAndIds = this.getCookies()
      if (emailAndIds)
        this.cachedEmail = emailAndIds.email
    }
    return this.cachedEmail
  }

  /**
   * Set cookies for the 'email', 'userId' and 'sessionId'.
   * 
   * @param {Object} values Set cookies for the properties in this object.
   * @param {int} days      The number of days in which the cookies are to expire.
   */
  setCookies(values, days) {
    var d = new Date()
    d.setDate(d.getDate() + days)
    var expiresAndPath = '; expires=' + d.toUTCString() + '; path=/'
    for (var key in values) {
      document.cookie = key + '=' + values[key] + expiresAndPath
    }
  }

  /**
   * Get the cookies containing the session details.
   * 
   * @return Dictionary containing keys 'email', 'userId', 'sessionId' or null if no information can be found.
   */
  getCookies() {
    var emailAndIds = {};
    var allCookies = document.cookie;
    var namesAndValues = allCookies.split(';');
    var count = 0;
    for (var i = 0; i < namesAndValues.length; ++i) {
      var nameAndValue = namesAndValues[i].split('=');
      if (nameAndValue.length == 2) {
        switch (nameAndValue[0].trim()) {
          case 'email':
            emailAndIds['email'] = nameAndValue[1];
            ++count;
            break;
          case 'userId':
            emailAndIds['userId'] = nameAndValue[1];
            ++count;
            break;
          case 'sessionId':
            emailAndIds['sessionId'] = nameAndValue[1];
            ++count;
            break;
        }
      }
    }

    if (count != 3) 
      return null;
    else
      return emailAndIds;
  }

  /** 
   * Get a list of the users.
   */
  async getUsers(callback) {
    var userList = []

    await m.request({
      method: 'GET',
      url: '/users'
    }).then(function(response) {
      userList = response.users
    })

    return userList
  }
}

const UserModelSingleton = new UserModel()

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
    if (!UserModelSingleton.addAuthentication(fields)) 
      return false

    var authenticated = true
    await m.request({
      method: "PUT",
      url: `/issues/${issueId}`,
      data: fields
    }).catch(function(error) {
      if (error.status_code == 401)
        authenticated = false
    })
    if (!authenticated) return false

    return await this.loadIssue(issueId)
  }
  async createIssue(fields) {
    if (!UserModelSingleton.addAuthentication(fields)) 
      return false

    var authenticated = true
    await m.request({
      method: "POST",
      url: `/issues`,
      data: fields
    }).catch(function(error) {
      if (error.status_code == 401)
        authenticated = false
    })
    if (!authenticated) return false

    return await this.loadIssues()
  }
  async getDashboardStatistics() {
    return await m.request({
      method: "GET",
      url: '/dashboard'
    })
  }
}

const IssuesModelSingleton = new IssuesModel()

module.exports = {IssuesModelSingleton, UserModelSingleton}
