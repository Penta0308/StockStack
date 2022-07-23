package kr.codenu.stockstack.core

import com.kotlindiscord.kord.extensions.ExtensibleBot
import com.kotlindiscord.kord.extensions.utils.env
import dev.kord.common.entity.Snowflake
import kr.codenu.stockstack.core.extensions.BasicExtension
import kr.codenu.stockstack.core.extensions.AdminExtension

object StockStackApp {
    val ADMINSERVER_ID = Snowflake(env("ADMINSERVER_ID"))
    private val DISCORD_TOKEN = env("DISCORD_TOKEN")
    lateinit var bot: ExtensibleBot

    suspend fun start() {
        bot = ExtensibleBot(DISCORD_TOKEN) {
            // chatCommands { enabled = true }
            // slashCommands { enabled = true}
            extensions {
                add(::BasicExtension)
                add(::AdminExtension)
            }
        }

        bot.start()
    }
}