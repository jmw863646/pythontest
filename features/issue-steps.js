const assert = require('assert')
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
})

Given('a browser', async function() {
  this.browser = new Nightmare({show: true})
})

Given("I'd like to raise a bug with a name that hasn't been used before", function () {
  this.issue = {
    title: randomString(),
    description: randomString()
  }
});

When('I raise the bug', async function () {
  await this.browser.goto('http://localhost:8640#!/issues/create')
  await this.browser.type('#title-input', this.issue.title)
  await this.browser.type('#description-input', this.issue.description)
  await this.browser.click('#save-button')
});

Then('my bug should appear in the list', async function () {
  await this.browser.goto('http://localhost:8640/#!/issues')
  let foundInList = await this.browser.evaluate(title => {
    let rows = document.querySelectorAll('table tr')
    for (let row of rows) {
      let titleCell = row.querySelector('.title-cell a')
      if (titleCell.innerText === title) return true
    }
  }, this.issue.title)
  assert(foundInList)
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
  await this.browser.click('#closed-input')
  await this.browser.type('#description-input', ' Fixed.')
  await this.browser.click('#save-button')
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
  assert.equal(this.issue.description + " Fixed.", description)
});
