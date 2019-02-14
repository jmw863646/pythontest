const assert = require('assert')
const { Before, After, Given, When, Then } = require('cucumber')
const Nightmare = require('nightmare')

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
