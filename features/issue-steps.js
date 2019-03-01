const assert = require('assert')
const fs = require('fs')
const { Before, After, Given, When, Then } = require('cucumber')
const Nightmare = require('nightmare')
const DateTimeRE = RegExp('^\\d{4}-\\d{2}-\\d{2}T\\d{2}:\\d{2}:\\d{2}$')

function randomString() {
  return Math.floor((Math.random() * (36 ** 10))).toString(36)
}

function findRow(table, colNumber, value) {
  if (table != null) {
    for (let row of table.querySelectorAll('tr')) {
      let cols = row.querySelectorAll(td)
      if (cols[colNumber].text() == value) return cols
    }
  }
}

After(async function(scenario) {
  if (this.browser) {
    if (scenario.result.status === 'failed') {
      let cleanName = scenario.pickle.name.replace(/[^\w]/g, '_')
      await this.browser.screenshot(`screenshots/${cleanName}.png`)
      await this.browser.html(`screenshots/${cleanName}.html`)
    }
    await this.browser.end()
  }
});

Given('a browser', async function() {
  this.browser = new Nightmare({show: true, width: 1024, height: 1024, typeInterval: 50})
});

Given('screenshots folder exists', function() {
  assert.ok(fs.existsSync('screenshots'), "Expecting the 'screenshots' directory to exist")
});

When('I open the website', async function() {
  await this.browser
    .goto('http://localhost:8640/')
});

Then('I should be able to login', async function() {
  var counts = await this.browser.evaluate(function() {
    var elements = document.querySelectorAll("a[href='#!/login']")
    var loginCount = elements.length
    elements = document.querySelectorAll("a[href='#!/create']")
    return [ loginCount, elements.length ]
  })

  assert.equal(counts[0], 1, "The login button should have reappeared")
  assert.equal(counts[1], 0, "The create button should have disappeared")
});

Given("I'd like to create some users", function() {
  this.user1 = {email: randomString() + '@gmail.com', password: randomString() }
  this.user2 = {email: randomString() + '@gmail.com', password: randomString() }
  this.user3 = {email: randomString() + '@gmail.com', password: randomString() }
});

When('I register a new user and login', {timeout: 20000}, async function() {
  await this.browser
    .goto('http://localhost:8640/#!/register')
    .type('#email-input', this.user1.email)
    .type('#password-input', this.user1.password)
    .click('#register-button')
    .wait('#login-button')
    .type('#email-input', this.user1.email)
    .type('#password-input', this.user1.password)
    .click('#login-button')
});

Then('should be logged in as user1', async function () {
  await this.browser.wait('div.container > table.table')

  var counts = await this.browser.evaluate(function() {
    var elements = document.querySelectorAll("button#logout-button")
    var logoutCount = elements.length
    elements = document.querySelectorAll("a[href='#!/issues/create']")
    return [ logoutCount, elements.length ]
  })

  assert.equal(counts[0], 1, "The logout button should have reappeared")
  assert.equal(counts[1], 1, "The create button should have appeared")
});

When('the page is refreshed', async function() {
  await this.browser.refresh()
});

Then('should still be logged in', async function() {
  await this.browser.wait('div.container > table.table')

  var counts = await this.browser.evaluate(function() {
    var elements = document.querySelectorAll("button#logout-button")
    var logoutCount = elements.length
    elements = document.querySelectorAll("a[href='#!/issues/create']")
    return [ logoutCount, elements.length ]
  })

  assert.equal(counts[0], 1, "The logout button should have reappeared")
  assert.equal(counts[1], 1, "The create button should have appeared")
});

Given("I'd like to raise bug with names that haven't been used before", function () {
  this.issue1 = {
    title: randomString(),
    description: randomString()
  }
  this.issue2 = {
    title: randomString(),
    description: randomString()
  }
});

When('I raise the bug', async function () {
  await this.browser
    .goto('http://localhost:8640#!/issues/create')
    .click("a[href='#!/issues/create']")
    .wait('#title-input')
    .wait('#description-input')
    .wait('#save-button')
    .type('#title-input', this.issue1.title)
    .type('#description-input', this.issue1.description)
    .click('#save-button')
});

Then('my bug should appear in the list', async function () {
  await this.browser.wait('div.container > table.table')
  let foundInList = await this.browser.evaluate(title => {
    let rows = document.querySelectorAll('table tr')
    for (let row of rows) {
      let titleCell = row.querySelector('.title-cell a')
      if (titleCell.innerText === title) return true
    }
  }, this.issue1.title)
  assert.ok(foundInList)
});

When('I view the description of the bug', async function () {
  await this.browser.wait('div.container > table.table')

  await this.browser.evaluate(title => {
    let rows = document.querySelectorAll('table tr')
    for (let row of rows) {
      let titleCell = row.querySelector('.title-cell a')
      if (titleCell.innerText === title) titleCell.click()
    }
  }, this.issue1.title)
});

Then('the description should match', async function () {
  this.browser.wait('p.description')
  let description = await this.browser.evaluate(() => {
    return document.querySelector('p.description').innerText
  })
  assert.equal(this.issue1.description, description)
});

When('I edit the existing bug', async function () {
  await this.browser.click('.btn-primary')
});

Then('the title should match', async function() {
  this.browser.wait('#title-input')
  let title = await this.browser.evaluate(() => {
    return document.querySelector('#title-input').value
  })
  assert.equal(this.issue1.title, title)
})

When('I change the description, close the bug and save', async function() {
  this.browser
    .wait('#title-input')
    .wait('#description-input')
    .wait('#save-button')
    .click('#closed-input')
    .type('#description-input', ' Fixed.')
    .click('#save-button')
})

Then('my bug should appear in the list closed', async function() {
  await this.browser.goto('http://localhost:8640/#!/issues')
  let closedInList = await this.browser.evaluate(title => {
    let rows = document.querySelectorAll('table tr')
    for (let row of rows) {
      let titleCell = row.querySelector('.title-cell a')
      if (titleCell.innerText === title) {
        let closedCell = row.querySelector('.closed-cell')
        return closedCell.innerText
      }
    }
  }, this.issue1.title)
  assert.ok(closedInList)
  assert.ok(DateTimeRE.test(closedInList), "The value of 'closed' doesn't look like a datetime")
});

When('I view the description of the bug again', async function () {
  await this.browser.evaluate(title => {
    let rows = document.querySelectorAll('table tr')
    for (let row of rows) {
      let titleCell = row.querySelector('.title-cell a')
      if (titleCell.innerText === title) titleCell.click()
    }
  }, this.issue1.title)
});

Then('the description should be updated', async function () {
  this.browser.wait('p.description')
  let description = await this.browser.evaluate(() => {
    return document.querySelector('p.description').innerText
  })
  assert.ok(description.endsWith('Fixed.'), "Description should now end in 'Fixed.'")
});

When('I logout', async function() {
  this.browser
    .goto('http://localhost:8640/')
    .click('#logout-button')
    .wait('#navbar-login-button')
})

When('I raise a bug while not logged in', async function() {
  await this.browser
    .goto('http://localhost:8640#!/issues/create')
    .type('#title-input', this.issue2.title)
    .type('#description-input', this.issue2.description)
    .click('#save-button')
});

Then('should ask me to login', async function() {
  await this.browser.wait('#login-button')

  var url = await this.browser
    .evaluate(() => { return document.URL; })
  assert.ok(url.endsWith('/login'), 'Should have navigated to the login page')
})

Given('edit an existing bug', async function() {
  var link = await this.browser
    .goto('http://localhost:8640/#!/issues')
    .evaluate(() => {
      return document.querySelector("td[class='title-cell'] > a").href
    })

  await this.browser.goto(link + '/edit')
});

When('I change the description, close the bug and save while not logged in', async function() {
  this.browser
    .wait('#description-input')
    .type('#description-input', ' Fixed.')
    .click('#save-button')
});

Given("I've registered some new users", async function() {
  await this.browser
    .click('a#register-link')
    .wait('#email-input')
    .wait('#password-input')
    .wait('#register-button')
    .type('#email-input', this.user2.email)
    .type('#password-input', this.user2.password)
    .click('#register-button')
    .wait('a#register-link')
    .click('a#register-link')
    .type('#email-input', this.user3.email)
    .type('#password-input', this.user3.password)
    .click('#register-button')
})

When('I login as user1', async function() {
  await this.browser
    .wait('#email-input')
    .wait('#password-input')
    .wait('#login-button')
    .type('#email-input', this.user1.email)
    .type('#password-input', this.user1.password)
    .click('#login-button')
})

Then('the bug should not be assigned', async function() {
  await this.browser.wait('p.description')
  
  let creatorAssignee = await this.browser.evaluate(() => {
    let ddElements = [].slice.call(document.querySelectorAll('dl > dd.col-sm-3:nth-of-type(2)'))
    return ddElements.map(x => x.innerText)
  })

  assert.equal(creatorAssignee.length, 2)
  assert.equal(creatorAssignee[0], this.user1.email, 'Check the creator is correct')
  assert.ok(!creatorAssignee[1], 'Should not be assigned')
})

When(/^the bug is ((?:un|)assigned) and saved$/, async function(action) {
  assigneeEmail = (action == 'assigned') ? this.user2.email : '<unassigned>'

  // Need to wait until the select element has been populated with two or more option elements
  let assigneeId = await this.browser
    .wait('select#assignee-input > option:nth-of-type(2)')
    .evaluate((email) => {
      let options = document.querySelectorAll('select#assignee-input > option')
      for (let opt of options) {
        if (opt.innerText == email) return opt.value;
      }
      return null
    }, assigneeEmail)
  assert.ok(assigneeId, 'Should have found our user')

  await this.browser
    .select('select#assignee-input', assigneeId)
    .click('.btn-primary')
})

Then('the bug should be assigned', async function() {
  await this.browser.wait('p.description')
  
  let creatorAssignee = await this.browser.evaluate(() => {
    let ddElements = [].slice.call(document.querySelectorAll('dl > dd.col-sm-3:nth-of-type(2)'))
    return ddElements.map(x => x.innerText)
  })

  assert.equal(creatorAssignee.length, 2)
  assert.equal(creatorAssignee[0], this.user1.email, 'Check the creator is correct')
  assert.equal(creatorAssignee[1], this.user2.email, 'Check the issue is assigned')
})
