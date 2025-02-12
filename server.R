# Define Server
server <- function(input, output, session) {
  
  # Connect to DuckDB
  db_connection <- tryCatch({
    dbConnect(duckdb::duckdb(), dbdir = "cohort.duckdb")
  }, error = function(e) {
    flog.error("Error connecting to DuckDB: %s", e$message)
    NULL  # Prevent crash
  })
  
  uploaded_data <- reactiveVal(list())
  criteria_count <- reactiveVal(1)
  
  # Track if files are uploaded
  output$filesUploaded <- reactive({
    !is.null(input$main) && nrow(input$main) > 0
  })
  outputOptions(output, "filesUploaded", suspendWhenHidden = FALSE)
  
  # Handle File Uploads
  observeEvent(input$main, {
    req(input$main)
    
    temp_data <- list()
    for (i in seq_along(input$main$name)) {
      tryCatch({
        if (grepl("\\.parquet$", input$main$name[i])) {
          temp_data[[input$main$name[i]]] <- input$main$datapath[i]
        } else if (grepl("\\.csv$", input$main$name[i])) {
          temp_data[[input$main$name[i]]] <- input$main$datapath[i]
        }
      }, error = function(e) {
        flog.error("Error reading file %s: %s", input$main$name[i], e$message)
      })
    }
    
    if (length(temp_data) > 0) {
      uploaded_data(temp_data)
    } else {
      flog.error("No valid data files were uploaded.")
    }
  })
  
  # Generate table choices dynamically
  table_choices <- reactive({
    files <- names(uploaded_data())
    cleaned_names <- gsub("\\.(csv|parquet)$", "", files, ignore.case = TRUE)
    return(cleaned_names)
  })
  
  ### ---------------------- Cohort Entry Selection ---------------------- ###
  output$cohort_entry_ui <- renderUI({
    num_criteria <- criteria_count()
    criteria_ui <- lapply(1:num_criteria, function(i) {
      fluidRow(
        tags$h5(paste("Cohort Entry Event", i)),
        selectInput(paste0("cohort_entry_events_", i), "Select Table",
                    choices = table_choices(), selected = NULL, multiple = FALSE),
        selectInput(paste0("cohort_column_selection_", i), "Select Column",
                    choices = c(""), selected = NULL, multiple = FALSE),
        uiOutput(paste0("cohort_dynamic_filter_ui_", i))
      )
    })
    do.call(tagList, criteria_ui)
  })
  
  ### ---------------------- Inclusion Criteria Selection ---------------------- ###
  output$inclusion_criteria_ui <- renderUI({
    num_criteria <- criteria_count()
    criteria_ui <- lapply(1:num_criteria, function(i) {
      fluidRow(
        tags$h5(paste("Inclusion Criteria", i)),
        selectInput(paste0("inclusion_criteria_events_", i), "Select Table",
                    choices = table_choices(), selected = NULL, multiple = FALSE),
        selectInput(paste0("inclusion_column_selection_", i), "Select Column",
                    choices = c(""), selected = NULL, multiple = FALSE),
        uiOutput(paste0("inclusion_dynamic_filter_ui_", i))
      )
    })
    do.call(tagList, criteria_ui)
  })
  
  ### ---------------------- Exclusion Criteria Selection ---------------------- ###
  output$exclusion_criteria_ui <- renderUI({
    num_criteria <- criteria_count()
    criteria_ui <- lapply(1:num_criteria, function(i) {
      fluidRow(
        tags$h5(paste("Exclusion Criteria", i)),
        selectInput(paste0("exclusion_criteria_events_", i), "Select Table",
                    choices = table_choices(), selected = NULL, multiple = FALSE),
        selectInput(paste0("exclusion_column_selection_", i), "Select Column",
                    choices = c(""), selected = NULL, multiple = FALSE),
        uiOutput(paste0("exclusion_dynamic_filter_ui_", i))
      )
    })
    do.call(tagList, criteria_ui)
  })
  
  ### ---------------------- Fetch Column Names Dynamically ---------------------- ###
  update_columns <- function(event_prefix, column_prefix) {
    observe({
      num_criteria <- criteria_count()
      for (i in 1:num_criteria) {
        local({
          current_i <- i
          observeEvent(input[[paste0(event_prefix, current_i)]], {
            req(input[[paste0(event_prefix, current_i)]])
            
            selected_cleaned_table <- input[[paste0(event_prefix, current_i)]]
            full_file_names <- names(uploaded_data())
            cleaned_names <- gsub("\\.(csv|parquet)$", "", full_file_names, ignore.case = TRUE)
            
            selected_table <- full_file_names[which(cleaned_names == selected_cleaned_table)]
            selected_path <- uploaded_data()[[selected_table]]
            
            query <- paste0("SELECT * FROM read_parquet('", selected_path, "') LIMIT 1")
            col_names <- tryCatch({
              dbGetQuery(db_connection, query)
            }, error = function(e) {
              flog.error("Error fetching column names for %s: %s", selected_table, e$message)
              NULL
            })
            
            if (!is.null(col_names) && ncol(col_names) > 0) {
              updateSelectInput(session, paste0(column_prefix, current_i), choices = colnames(col_names))
            }
          })
        })
      }
    })
  }
  
  update_columns("cohort_entry_events_", "cohort_column_selection_")
  update_columns("inclusion_criteria_events_", "inclusion_column_selection_")
  update_columns("exclusion_criteria_events_", "exclusion_column_selection_")
  
  ### ---------------------- Generate Dynamic Filters ---------------------- ###
  # Function to generate dynamic filters when a column is selected
  generate_filters <- function(event_prefix, column_prefix, filter_prefix) {
    observe({
      num_criteria <- criteria_count()
      
      for (i in 1:num_criteria) {
        local({
          current_i <- i  # Capture the loop variable properly
          
          observeEvent(input[[paste0(column_prefix, current_i)]], {
            req(input[[paste0(column_prefix, current_i)]])
            
            selected_column <- input[[paste0(column_prefix, current_i)]]
            selected_table <- input[[paste0(event_prefix, current_i)]]
            
            # Ensure we are using the full table path
            full_file_names <- names(uploaded_data())
            cleaned_names <- gsub("\\.(csv|parquet)$", "", full_file_names, ignore.case = TRUE)
            selected_table_full <- full_file_names[which(cleaned_names == selected_table)]
            selected_path <- uploaded_data()[[selected_table_full]]
            
            flog.info("Resolved table name: %s -> %s", selected_table, selected_table_full)
            
            # **REGISTER TABLE IN DUCKDB**
            duckdb_table_name <- paste0("temp_", gsub("\\W", "_", selected_table_full)) # Clean name
            dbExecute(db_connection, paste0("CREATE OR REPLACE TABLE ", duckdb_table_name, " AS SELECT * FROM read_parquet('", selected_path, "')"))
            
            # **FIXED TYPE QUERY**
            type_query <- paste0("PRAGMA table_info(", duckdb_table_name, ")")
            
            flog.info("Executing type query: %s", type_query)  # Debug log
            
            column_info <- tryCatch({
              dbGetQuery(db_connection, type_query)
            }, error = function(e) {
              flog.error("Error fetching column info for %s: %s", selected_column, e$message)
              return(NULL)
            })
            
            if (is.null(column_info) || nrow(column_info) == 0) {
              flog.warn("Column type query returned no results for %s", selected_column)
              return(NULL)
            }
            
            # Extract the type of the selected column
            column_type <- column_info$type[column_info$name == selected_column]
            
            flog.info("DuckDB inferred type for %s: %s", selected_column, column_type)
            
            isolate({
              if (is.null(column_type) || length(column_type) == 0) {
                flog.warn("Type inference failed for %s. UI will not be updated.", selected_column)
                return(NULL)
              }
              
              # **DATE FILTER**
              if (grepl("DATE|TIMESTAMP", column_type, ignore.case = TRUE)) {
                flog.info("Generating Date Filter UI for %s", selected_column)
                output[[paste0(filter_prefix, current_i)]] <- renderUI({
                  dateRangeInput(paste0("date_filter_", current_i), "Select Date Range:")
                })
                
                # **NUMERIC SLIDER FILTER**
              } else if (grepl("INT|DOUBLE|NUMERIC|FLOAT", column_type, ignore.case = TRUE)) {
                range_query <- paste0("
                SELECT MIN(", selected_column, ") AS min_val, MAX(", selected_column, ") AS max_val 
                FROM ", duckdb_table_name, "
              ")
                
                flog.info("Executing range query: %s", range_query)  # Debug log
                
                num_range <- tryCatch({
                  dbGetQuery(db_connection, range_query)
                }, error = function(e) {
                  flog.error("Error fetching numeric range for %s: %s", selected_column, e$message)
                  return(NULL)
                })
                
                if (!is.null(num_range) && nrow(num_range) > 0) {
                  flog.info("Min: %s, Max: %s", num_range$min_val, num_range$max_val)  # Debug log
                  
                  flog.info("Generating Numeric Filter UI for %s", selected_column)
                  output[[paste0(filter_prefix, current_i)]] <- renderUI({
                    sliderInput(paste0("numeric_filter_", current_i), "Select Range:", 
                                min = num_range$min_val, 
                                max = num_range$max_val, 
                                value = c(num_range$min_val, num_range$max_val))
                  })
                }
                
                # **CATEGORICAL DROPDOWN FILTER**
              } else {
                unique_query <- paste0("
                SELECT DISTINCT ", selected_column, " 
                FROM ", duckdb_table_name, "
              ")
                
                flog.info("Executing unique values query: %s", unique_query)  # Debug log
                
                unique_values <- tryCatch({
                  dbGetQuery(db_connection, unique_query)[[selected_column]]
                }, error = function(e) {
                  flog.error("Error fetching unique values for %s: %s", selected_column, e$message)
                  return(NULL)
                })
                
                if (!is.null(unique_values) && length(unique_values) > 0) {
                  flog.info("Unique values for %s: %s", selected_column, toString(unique_values))  # Debug log
                  
                  flog.info("Generating Categorical Filter UI for %s", selected_column)
                  output[[paste0(filter_prefix, current_i)]] <- renderUI({
                    selectInput(paste0("categorical_filter_", current_i), "Select Values:", 
                                choices = unique_values, 
                                selected = unique_values[1], multiple = TRUE)
                  })
                }
              }
            })  # End of isolate()
          })
        })
      }
    })
  }
  
  # Apply to Cohort, Inclusion, and Exclusion Filters
  generate_filters("cohort_entry_events_", "cohort_column_selection_", "cohort_dynamic_filter_ui_")
  generate_filters("inclusion_criteria_events_", "inclusion_column_selection_", "inclusion_dynamic_filter_ui_")
  generate_filters("exclusion_criteria_events_", "exclusion_column_selection_", "exclusion_dynamic_filter_ui_")
  
  # Close DB connection on exit
  onStop(function() {
    dbDisconnect(db_connection)
  })
}
