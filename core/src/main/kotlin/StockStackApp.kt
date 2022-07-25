package kr.codenu.stockstack.core

import com.kotlindiscord.kord.extensions.DISCORD_GREEN
import com.kotlindiscord.kord.extensions.ExtensibleBot
import com.kotlindiscord.kord.extensions.i18n.SupportedLocales
import com.kotlindiscord.kord.extensions.utils.env
import com.mchange.v2.c3p0.ComboPooledDataSource
import dev.kord.common.entity.Snowflake
import kr.codenu.stockstack.core.extensions.AdminExtension
import kr.codenu.stockstack.core.extensions.BasicExtension
import kr.codenu.stockstack.core.extensions.UserExtension

object StockStackApp {
    val ADMINSERVER_ID = Snowflake(env("ADMINSERVER_ID"))
    private val DISCORD_TOKEN = env("DISCORD_TOKEN")
    private val DB_USER = env("DB_USER")
    private val DB_PASSWORD = env("DB_PASSWORD")
    lateinit var bot: ExtensibleBot
    lateinit var datasource: ComboPooledDataSource

    suspend fun start() {
        bot = ExtensibleBot(DISCORD_TOKEN) {
            // chatCommands { enabled = true }
            applicationCommands {
                defaultGuild = ADMINSERVER_ID
                enabled = true
            }

            i18n {
                defaultLocale = SupportedLocales.ENGLISH
            }

            extensions {
                help {
                    colour { DISCORD_GREEN }
                    deletePaginatorOnTimeout = true
                    deleteInvocationOnPaginatorTimeout = true
                }

                sentry {}

                add(::BasicExtension)
                add(::AdminExtension)
                add(::UserExtension)
            }
        }

        datasource = ComboPooledDataSource()
        datasource.jdbcUrl = "jdbc:postgresql://localhost/stockstack?currentSchema=stockstack"
        datasource.user = DB_USER
        datasource.password = DB_PASSWORD

        bot.start()
    }
}