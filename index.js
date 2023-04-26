const axios = require('axios');
const cheerio = require('cheerio');
const normalizeWhitespace = require('normalize-html-whitespace');
const TurndownService = require('turndown')

require('dotenv').config();
const nodemailer = require("nodemailer");

const destUrl = process.env.WEBHOOK;
const sourceUrl = process.env.SOURCE_URL;
const apiPass = process.env.SENDGRID_API_KEY;
const toEmail = process.env.TO_EMAIL;
const fromEmail = process.env.FROM_EMAIL;

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

function sendEmailReport(data, apiPass, toEmail, fromEmail) {
  let transporter = nodemailer.createTransport({
    host: 'smtp.sendgrid.net',
    port: 465,
    auth: {
        user: "apikey",
        pass: apiPass
    }
  });

  transporter.sendMail({
    from: 'BinJuice <' + fromEmail + '>', // verified sender email
    to: toEmail, // recipient email
    subject: "Bin collection for the week", // Subject line
    text: data // plain text body,
  }, function(error, info){
    if (error) {
      console.log(error);
    } else {
      console.log('Email sent: ' + info.response);
    }
  });
}

getSourceData(sourceUrl)
  .then(data => {
    sendEmailReport(data, apiPass, toEmail, fromEmail)      
    // postToWebhook(destUrl, data)
      // .then(data => {
      //   console.log(data);
      // });
  });