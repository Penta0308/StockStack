package kr.codenu.stockstack.core.extensions

import com.kotlindiscord.kord.extensions.extensions.Extension
import com.kotlindiscord.kord.extensions.extensions.publicSlashCommand
import com.kotlindiscord.kord.extensions.types.respond

class BasicExtension: Extension() {
    override val name = "basic"
    override suspend fun setup() {
        publicSlashCommand {
            name = "ping"
            description = "tick-tock"

            action {
                respond {
                    content = "pong"
                }
            }
        }
    }
}