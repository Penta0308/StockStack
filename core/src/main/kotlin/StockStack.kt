package kr.codenu.stockstack.core

suspend fun main(args: Array<String>) {
    println("Hello World!")
    println("Program arguments: ${args.joinToString()}")

    StockStackApp.start()
}