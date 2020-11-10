const axios = require('axios');
const cheerio = require('cheerio');
const normalizeWhitespace = require('normalize-html-whitespace');
const TurndownService = require('turndown')

const destUrl = process.env.WEBHOOK;
const sourceUrl = process.env.SOURCE_URL;

function getSourceData(url) {
  return axios.get(url)
      .then(response => {
        const $ = cheerio.load(response.data);
        const turndownService = new TurndownService();

        return turndownService.turndown(normalizeWhitespace($('.page-content .col-2-3').html()));    
      })
      .catch(error => {
        console.log(error);
      });
}

function postToWebhook(url, data) {
  return axios.post(url, {
      data: data
    })
    .then(function (response) {
      return 'Done, with response code ' + response.status;
    })
    .catch(function (error) {
      console.log(error);
    });
}

getSourceData(sourceUrl)
  .then(data => {
    postToWebhook(destUrl, data)
      .then(data => {
        console.log(data);
      });
  });