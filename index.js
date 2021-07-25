//@ts-check
const Discord = require("discord.js");
const client = new Discord.Client();

require("dotenv").config();


client.on('ready', function() {
  console.log("Bot is running!")
})

client.on("message", function(msg) {
  if (msg.content === "ping") {
    msg.reply("pong");
  }
});


client.login(process.env.TOKEN);  
