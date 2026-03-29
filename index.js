const { Client, GatewayIntentBits } = require("discord.js");
const token = process.env.DISCORD_BOT_TOKEN;
const guildId = process.env.DISCORD_GUILD_ID;

if (!token) {
  throw new Error("環境変数 DISCORD_BOT_TOKEN が未設定です。");
}

if (!guildId) {
  throw new Error("環境変数 DISCORD_GUILD_ID が未設定です。");
}

const client = new Client({
  intents: [
    GatewayIntentBits.Guilds
  ]
});

client.once("clientReady", () => {
  console.log(`${client.user.tag} でログインしています。`);

  const pingCommand = {
    name: "ping",
    description: "Pong! を返します"
  };

  // guild command is reflected quickly for development.
  client.guilds.fetch(guildId)
    .then(guild => guild.commands.set([pingCommand]))
    .then(() => console.log("/ping コマンドを登録しました。"))
    .catch(err => console.error("コマンド登録に失敗しました:", err));
});

client.on("interactionCreate", async interaction => {
  if (!interaction.isChatInputCommand()) return;

  if (interaction.commandName === "ping") {
    await interaction.reply("Pong!");
  }
});

client.login(token);