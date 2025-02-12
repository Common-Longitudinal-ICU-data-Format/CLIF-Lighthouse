library(shiny)
library(DBI)
library(duckdb)
library(jsonlite)
library(arrow)
library(fst)
library(uuid)
library(futile.logger)  # Logging package

source("ui.R")
source("server.R")

options(shiny.maxRequestSize = 100 * 1024^4)

# Setup logger
flog.appender(appender.file("app.log"))  # Log to a file
flog.threshold(DEBUG)  # Set logging level

shinyApp(ui, server)