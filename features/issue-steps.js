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

Given("I'd like to register a user and login", function() {
  this.user = {email: randomString() + '@gmail.com', password: randomString() }
});

When('I register a new user and login', {timeout: 20000}, async function() {
  await this.browser
    .goto('http://localhost:8640/#!/register')
    .type('#email-input', this.user.email)
    .type('#password-input', this.user.password)
    .click('#register-button')
    .wait('#login-button')
    .type('#email-input', this.user.email)
    .type('#password-input', this.user.password)
    .click('#login-button')
});

Then('should be logged in as new user', async function () {
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

Given("I'd like to raise a bug with a name that hasn't been used before", function () {
  this.issue = {
    title: randomString(),
    description: randomString()
  }
});

When('I raise the bug', async function () {
  await this.browser
    .goto('http://localhost:8640#!/issues/create')
    .click("a[href='#!/issues/create']")
    .wait('#title-input, #description-input, #save-button')
    .type('#title-input', this.issue.title)
    .type('#description-input', this.issue.description)
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
  }, this.issue.title)
  assert.ok(foundInList)
});

When('I view the description of the bug', async function () {
  await this.browser.evaluate(title => {
    let rows = document.querySelectorAll('table tr')
    for (let row of rows) {
      let titleCell = row.querySelector('.title-cell a')
      if (titleCell.innerText === title) titleCell.click()
    }
  }, this.issue.title)
});

Then('the description should match', async function () {
  this.browser.wait('p.description')
  let description = await this.browser.evaluate(() => {
    return document.querySelector('p.description').innerText
  })
  assert.equal(this.issue.description, description)
});

When('I edit the existing bug', async function () {
  await this.browser.click('.btn-primary')
});

Then('the title should match', async function() {
  this.browser.wait('#title-input')
  let title = await this.browser.evaluate(() => {
    return document.querySelector('#title-input').value
  })
  assert.equal(this.issue.title, title)
})

When('I change the description, close the bug and save', async function() {
  this.browser
    .wait('#title-input, #description-input, #save-button')
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
  }, this.issue.title)
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
  }, this.issue.title)
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
    .type('#title-input', this.issue.title)
    .type('#description-input', this.issue.description)
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


