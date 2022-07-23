package kr.codenu.stockstack.core.extensions

import com.kotlindiscord.kord.extensions.extensions.Extension
import com.kotlindiscord.kord.extensions.extensions.publicSlashCommand
import com.kotlindiscord.kord.extensions.types.respond

import kr.codenu.stockstack.core.StockStackApp
import java.lang.management.ManagementFactory

class AdminExtension : Extension() {
    override val name = "admin"
    override suspend fun setup() {
        publicSlashCommand {
            name = "status"
            description = "tick-tock"
            guild(StockStackApp.ADMINSERVER_ID)

            action {
                respond {
                    content = "MEM %.2f G".format(
                        ManagementFactory.getMemoryMXBean().heapMemoryUsage.used * 1.0f / 0x100000
                    )
                }
            }
        }
    }
}