library(shiny)
library(DBI)
library(duckdb)
library(jsonlite)
library(arrow)
library(fst)
library(uuid)
library(futile.logger)  
library(magrittr)

source("ui.R")
source("server.R")

options(shiny.maxRequestSize = 100 * 1024^4)

# Setup logger
if (file.exists("app.log")) {
  file.remove("app.log")  # Delete old log file
}
flog.appender(appender.file("app.log"))  # Log to a file
flog.threshold(DEBUG)  # Set logging level

# Remove existing database 
if (file.exists("cohort.duckdb")) {
  file.remove("cohort.duckdb")
}

shinyApp(ui, server)