package kr.codenu.stockstack.core.extensions

import com.kotlindiscord.kord.extensions.components.components
import com.kotlindiscord.kord.extensions.components.ephemeralButton
import com.kotlindiscord.kord.extensions.components.linkButton
import com.kotlindiscord.kord.extensions.extensions.Extension
import com.kotlindiscord.kord.extensions.extensions.ephemeralSlashCommand
import com.kotlindiscord.kord.extensions.types.respond

import kr.codenu.stockstack.core.stockmarket.UserManager
import kr.codenu.stockstack.core.stockmarket.UserType

class UserExtension: Extension() {
    override val name = "user"
    override suspend fun setup() {
        ephemeralSlashCommand {
            name = "join"
            description = "Create Account"

            action {
                respond {
                    content = "pong"

                    components {
                        linkButton {
                            label = "Policy"
                            url = "https://example.com"
                        }
                        ephemeralButton {
                            label = "Agree!"
                            action {
                                val discordid = this.user.asUser().id.value
                                val username = "discord$discordid"
                                val userid = UserManager.create(username, UserType.HUMAN)
                                UserManager.create_discordcredential(userid, discordid)

                                respond {
                                    content = "Username $username Userid $userid"
                                }
                            }
                        }
                    }
                }
            }
        }
    }
}