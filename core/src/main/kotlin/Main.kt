package kr.codenu.stockstack.core

import dev.kord.common.annotation.KordPreview
import me.jakejmattson.discordkt.api.dsl.bot
import kotlin.io.println

@KordPreview
suspend fun main(args: Array<String>) {
    println("Hello World!")
    println("Program arguments: ${args.joinToString()}")

    bot(System.getenv("DISCORD_TOKEN")) {
        prefix {
            "s!"
        }
        re {
            //Allow a mention to be used in front of commands ('@Bot help`).
            allowMentionPrefix = true

            //Whether or not to generate documentation for registered commands.
            generateCommandDocs = true

            //Whether or not to show registered entity information on startup.
            showStartupLog = true

            //Whether or not to recommend commands when an invalid one is invoked.
            recommendCommands = true

            //Allow users to search for a command by typing 'search <command name>'.
            enableSearch = true

            //An emoji added when a command is invoked (use 'null' to disable this).
            commandReaction = Emojis.eyes

            //A color constant for your bot - typically used in embeds.
            theme = Color(0x00BFFF)

            //Configure the Discord Gateway intents for your bot.
            intents = Intents.nonPrivileged

            //Set bot permissions with a default value for all commands.
            permissions(commandDefault = Permissions.EVERYONE)
        }

        //An embed sent whenever someone solely mentions your bot ('@Bot').
        mentionEmbed {
            title = "Hello World"
            color = it.discord.configuration.theme?.kColor

            author {
                with(it.author) {
                    icon = avatar.url
                    name = tag
                    url = profileLink
                }
            }

            thumbnail {
                url = it.discord.kord.getSelf().avatar.url
            }

            footer {
                val versions = it.discord.versions
                text = "${versions.library} - ${versions.kord} - ${versions.kotlin}"
            }
            addField("Prefix", it.prefix())
        }

        //The Discord presence shown on your bot.
        presence {
            playing("쌓다")
        }

        //This is run once the bot has finished setup and logged in.
        onStart {
            val guilds = kord.guilds.toList().joinToString { it.name }
            println("Guilds: $guilds")
        }

        //Configure the locale for this bot.
        localeOf(Language.EN) {
            helpName = "Help"
            helpCategory = "Utility"
            commandRecommendation = "Recommendation: {0}"
        }
    }

    commands("Utility") {
        command("Ping") {
            description = "Check to see if the bot is online."
            execute {
                respond("Pong!")
            }
        }
    }

}