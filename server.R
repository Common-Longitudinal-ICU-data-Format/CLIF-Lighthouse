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
  cohort_criteria_count <- reactiveVal(1)
  inclusion_criteria_count <- reactiveVal(1)
  exclusion_criteria_count <- reactiveVal(1)
  
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
    num_criteria <- cohort_criteria_count()
    criteria_ui <- lapply(1:num_criteria, function(i) {
      fluidRow(
        tags$h5(paste("Cohort Entry Event", i)),
        selectizeInput(paste0("cohort_entry_events_", i), "Select Table",
                    choices = table_choices(), selected = NULL, multiple = FALSE),
        selectizeInput(paste0("cohort_column_selection_", i), "Select Column",
                    choices = c(""), selected = NULL, multiple = FALSE),
        uiOutput(paste0("cohort_dynamic_filter_ui_", i))
      )
    })
    do.call(tagList, criteria_ui)
  })
  
  ### ---------------------- Inclusion Criteria Selection ---------------------- ###
  output$inclusion_criteria_ui <- renderUI({
    num_criteria <- inclusion_criteria_count()
    criteria_ui <- lapply(1:num_criteria, function(i) {
      fluidRow(
        tags$h5(paste("Inclusion Criteria", i)),
        selectizeInput(paste0("inclusion_criteria_events_", i), "Select Table",
                    choices = table_choices(), selected = NULL, multiple = FALSE),
        selectizeInput(paste0("inclusion_column_selection_", i), "Select Column",
                    choices = c(""), selected = NULL, multiple = FALSE),
        uiOutput(paste0("inclusion_dynamic_filter_ui_", i))
      )
    })
    do.call(tagList, criteria_ui)
  })
  
  ### ---------------------- Exclusion Criteria Selection ---------------------- ###
  output$exclusion_criteria_ui <- renderUI({
    num_criteria <- exclusion_criteria_count()
    criteria_ui <- lapply(1:num_criteria, function(i) {
      fluidRow(
        tags$h5(paste("Exclusion Criteria", i)),
        selectizeInput(paste0("exclusion_criteria_events_", i), "Select Table",
                    choices = table_choices(), selected = NULL, multiple = FALSE),
        selectizeInput(paste0("exclusion_column_selection_", i), "Select Column",
                    choices = c(""), selected = NULL, multiple = FALSE),
        uiOutput(paste0("exclusion_dynamic_filter_ui_", i))
      )
    })
    do.call(tagList, criteria_ui)
  })
  
  ### ---------------------- Fetch Column Names Dynamically ---------------------- ###
  update_columns <- function(event_prefix, column_prefix) {
    observe({
      num_criteria <- cohort_criteria_count()
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
              # Exclude patient_id and hospitalization_id from choices
              filtered_col_names <- colnames(col_names)[!colnames(col_names) %in% c("patient_id", "hospitalization_id")]
              updateSelectizeInput(session, paste0(column_prefix, current_i), choices = filtered_col_names)
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
      num_criteria <- cohort_criteria_count()
      
      for (i in 1:num_criteria) {
        local({
          current_i <- i  # Capture the loop variable properly
          
          observeEvent(input[[paste0(column_prefix, current_i)]], {
            req(input[[paste0(column_prefix, current_i)]])
            
            invalidateLater(1000, session)  # Force UI updates every second

            selected_column <- input[[paste0(column_prefix, current_i)]]
            selected_table <- input[[paste0(event_prefix, current_i)]]
            
            # Ensure we are using the full table path
            full_file_names <- names(uploaded_data())
            cleaned_names <- gsub("\\.(csv|parquet)$", "", full_file_names, ignore.case = TRUE)
            selected_table_full <- full_file_names[which(cleaned_names == selected_table)]
            selected_path <- uploaded_data()[[selected_table_full]]
            
            # **REGISTER TABLE IN DUCKDB**
            duckdb_table_name <- selected_table  # Use cleaned table name
            flog.info("Registering DuckDB table: %s from file %s", duckdb_table_name, selected_table_full)
            
            dbExecute(db_connection, paste0("CREATE OR REPLACE TABLE ", duckdb_table_name, 
                                            " AS SELECT * FROM read_parquet('", selected_path, "')"))
            
            # **Fetch Column Type**
            type_query <- paste0("PRAGMA table_info(", duckdb_table_name, ")")
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

              flog.info("Rendering UI for column: %s of type: %s", selected_column, column_type)

              # Ensure the UI is refreshed
              output[[paste0(filter_prefix, current_i)]] <- renderUI({
                
                # **DATE FILTER**
                if (grepl("DATE|TIMESTAMP", column_type, ignore.case = TRUE)) {
                  flog.info("Generating Date Filter UI for %s", selected_column)
                  dateRangeInput(paste0("date_filter_", current_i), "Select Date Range:")
                
                # **NUMERIC SLIDER FILTER**
                } else if (grepl("INT|DOUBLE|NUMERIC|FLOAT", column_type, ignore.case = TRUE)) {
                  range_query <- paste0("
                    SELECT MIN(", selected_column, ") AS min_val, MAX(", selected_column, ") AS max_val 
                    FROM ", duckdb_table_name, "
                  ")

                  flog.info("Executing range query: %s", range_query)
                  
                  num_range <- tryCatch({
                    dbGetQuery(db_connection, range_query)
                  }, error = function(e) {
                    flog.error("Error fetching numeric range for %s: %s", selected_column, e$message)
                    return(NULL)
                  })
                  
                  if (!is.null(num_range) && nrow(num_range) > 0) {
                    flog.info("Min: %s, Max: %s", num_range$min_val, num_range$max_val)
                    flog.info("Generating Numeric Filter UI for %s", selected_column)
                    sliderInput(paste0("numeric_filter_", current_i), "Select Range:", 
                                min = num_range$min_val, 
                                max = num_range$max_val, 
                                value = c(num_range$min_val, num_range$max_val))
                  } else {
                    return(NULL)  # Avoid displaying empty UI
                  }
                
                # **CATEGORICAL DROPDOWN FILTER**
                } else {
                  unique_query <- paste0("
                    SELECT DISTINCT ", selected_column, " 
                    FROM ", duckdb_table_name, "
                  ")

                  flog.info("Executing unique values query: %s", unique_query)
                  
                  unique_values <- tryCatch({
                    dbGetQuery(db_connection, unique_query)[[selected_column]]
                  }, error = function(e) {
                    flog.error("Error fetching unique values for %s: %s", selected_column, e$message)
                    return(NULL)
                  })
                  
                  flog.info("Unique Values Retrieved: %s", toString(head(unique_values, 10)))
                  
                  if (!is.null(unique_values) && length(unique_values) > 0) {
                    flog.info("Generating Categorical Filter UI for %s", selected_column)
                    selectizeInput(paste0(filter_prefix, current_i), "Select Values:", 
                                   choices = unique_values, 
                                   selected = unique_values[1], multiple = TRUE)
                  } else {
                    return(NULL)  # Avoid displaying empty UI
                  }
                }
              })  # End of renderUI()

              # Force UI updates even if hidden
              outputOptions(output, paste0(filter_prefix, current_i), suspendWhenHidden = FALSE)
              
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
  
  # Handle Add Criteria for Cohort Entry
  observeEvent(input$add_criteria, {
    cohort_criteria_count(cohort_criteria_count() + 1)  # Increment cohort criteria count
  })
  
  # Handle Add Inclusion Criteria
  observeEvent(input$add_inclusion_criteria, {
    inclusion_criteria_count(inclusion_criteria_count() + 1)  # Increment inclusion criteria count
  })
  
  # Handle Add Exclusion Criteria
  observeEvent(input$add_exclusion_criteria, {
    exclusion_criteria_count(exclusion_criteria_count() + 1)  # Increment exclusion criteria count
  })
  
  # Handle Remove Last Criteria for Cohort Entry
  observeEvent(input$remove_criteria, {
    if (cohort_criteria_count() > 1) {
      cohort_criteria_count(cohort_criteria_count() - 1)  # Decrement cohort criteria count
    }
  })
  
  # Handle Remove Last Inclusion Criteria
  observeEvent(input$remove_inclusion_criteria, {
    if (inclusion_criteria_count() > 1) {
      inclusion_criteria_count(inclusion_criteria_count() - 1)  # Decrement inclusion criteria count
    }
  })
  
  # Handle Remove Last Exclusion Criteria
  observeEvent(input$remove_exclusion_criteria, {
    if (exclusion_criteria_count() > 1) {
      exclusion_criteria_count(exclusion_criteria_count() - 1)  # Decrement exclusion criteria count
    }
  })
  
  # Generate Cohort Entry Summary
  output$cohort_entry_summary <- renderUI({
    num_criteria <- cohort_criteria_count()
    criteria_summary <- lapply(1:num_criteria, function(i) {
      fluidRow(
        tags$h5(paste("Cohort Entry Event", i)),
        textOutput(paste0("cohort_entry_event_", i))
      )
    })
    do.call(tagList, criteria_summary)
  })
  
  # Create text outputs for each cohort entry event
  observe({
    num_criteria <- cohort_criteria_count()
    for (i in 1:num_criteria) {
      local({
        current_i <- i
        output[[paste0("cohort_entry_event_", current_i)]] <- renderText({
          selected_event <- input[[paste0("cohort_entry_events_", current_i)]]
          selected_column <- input[[paste0("cohort_column_selection_", current_i)]]
          selected_filter <- input[[paste0("cohort_dynamic_filter_ui_", current_i)]]
          
          if (is.null(selected_event) || selected_event == "") {
            return("No event selected.")
          }
          if (is.null(selected_column) || selected_column == "") {
            return(paste("Event:", selected_event, "- No column selected."));
          }
          if (is.null(selected_filter) || length(selected_filter) == 0) {
            return(paste("Event:", selected_event, "- Selected Column:", selected_column, "- No filter values selected."));
          }
          paste("Event:", selected_event, "- Selected Column:", selected_column, "- Filter Values:", toString(selected_filter))
        })
      })
    }
  })
  
  # Generate Inclusion Criteria Summary
  output$inclusion_criteria_summary <- renderUI({
    num_criteria <- inclusion_criteria_count()
    criteria_summary <- lapply(1:num_criteria, function(i) {
      fluidRow(
        tags$h5(paste("Inclusion Criteria", i)),
        textOutput(paste0("inclusion_criteria_event_", i))
      )
    })
    do.call(tagList, criteria_summary)
  })
  
  # Create text outputs for each inclusion criteria event
  observe({
    num_criteria <- inclusion_criteria_count()
    for (i in 1:num_criteria) {
      local({
        current_i <- i
        output[[paste0("inclusion_criteria_event_", current_i)]] <- renderText({
          selected_event <- input[[paste0("inclusion_criteria_events_", current_i)]]
          selected_column <- input[[paste0("inclusion_column_selection_", current_i)]]
          selected_filter <- input[[paste0("inclusion_dynamic_filter_ui_", current_i)]]
          
          if (is.null(selected_event) || selected_event == "") {
            return("No event selected.");
          }
          if (is.null(selected_column) || selected_column == "") {
            return(paste("Event:", selected_event, "- No column selected."));
          }
          if (is.null(selected_filter) || length(selected_filter) == 0) {
            return(paste("Event:", selected_event, "- Selected Column:", selected_column, "- No filter values selected."));
          }
          paste("Event:", selected_event, "- Selected Column:", selected_column, "- Filter Values:", toString(selected_filter))
        })
      })
    }
  })
  
  # Generate Exclusion Criteria Summary
  output$exclusion_criteria_summary <- renderUI({
    num_criteria <- exclusion_criteria_count()
    criteria_summary <- lapply(1:num_criteria, function(i) {
      fluidRow(
        tags$h5(paste("Exclusion Criteria", i)),
        textOutput(paste0("exclusion_criteria_event_", i))
      )
    })
    do.call(tagList, criteria_summary)
  })
  
  # Create text outputs for each exclusion criteria event
  observe({
    num_criteria <- exclusion_criteria_count()
    for (i in 1:num_criteria) {
      local({
        current_i <- i
        output[[paste0("exclusion_criteria_event_", current_i)]] <- renderText({
          selected_event <- input[[paste0("exclusion_criteria_events_", current_i)]]
          selected_column <- input[[paste0("exclusion_column_selection_", current_i)]]
          selected_filter <- input[[paste0("exclusion_dynamic_filter_ui_", current_i)]]
          
          if (is.null(selected_event) || selected_event == "") {
            return("No event selected.");
          }
          if (is.null(selected_column) || selected_column == "") {
            return(paste("Event:", selected_event, "- No column selected."));
          }
          if (is.null(selected_filter) || length(selected_filter) == 0) {
            return(paste("Event:", selected_event, "- Selected Column:", selected_column, "- No filter values selected."));
          }
          paste("Event:", selected_event, "- Selected Column:", selected_column, "- Filter Values:", toString(selected_filter))
        })
      })
    }
  })
  
  
  #################################### 
  cohort_definition_text <- reactiveVal("No cohort definition provided.")
  
  # Save Cohort Definition when button is clicked
  observeEvent(input$save_definition, {
    req(input$cohort_definition)  # Ensure input is not NULL
    cohort_definition_text(input$cohort_definition)  # Store input
    flog.info("Cohort definition saved: %s", input$cohort_definition)  # Debugging log
  })
  
  # Display Cohort Definition in Summary Tab
  output$cohort_definition_display <- renderText({
    cohort_definition_text()  # Return stored definition
  })
  
  filtered_data <- reactiveVal(NULL)
  # Render sample dataframe in Summary Tab
  observe({
    req(uploaded_data())
    
    num_criteria <- cohort_criteria_count()
    if (num_criteria < 1) return(NULL)
    
    # Get selected cohort entry table and column
    cohort_table <- input[[paste0("cohort_entry_events_", 1)]]
    cohort_column <- input[[paste0("cohort_column_selection_", 1)]]
    cohort_filter <- input[[paste0("cohort_dynamic_filter_ui_", 1)]]
    
    # Get selected inclusion criteria table (optional)
    inclusion_table <- input[[paste0("inclusion_criteria_events_", 1)]]
    
    if (is.null(cohort_table) || is.null(cohort_column) || is.null(cohort_filter)) {
      return(NULL)
    }
    
    # **Construct WHERE condition for cohort table**
    if (is.numeric(cohort_filter)) {
      condition <- paste0(cohort_column, " BETWEEN ", cohort_filter[1], " AND ", cohort_filter[2])
    } else if (is.character(cohort_filter)) {
      filter_values <- paste0("'", paste(cohort_filter, collapse = "','"), "'")
      condition <- paste0(cohort_column, " IN (", filter_values, ")")
    } else {
      return(NULL)
    }
    
    # **Handle Case: No Inclusion Table Selected**
    if (is.null(inclusion_table) || inclusion_table == "") {
      query <- paste0("SELECT * FROM ", cohort_table, " WHERE ", condition, " LIMIT 5")
      flog.info("Executing query (without inclusion table): %s", query)
    } else {
      # **Find common column ending with `_id`**
      get_id_columns <- function(table_name) {
        query <- paste0("PRAGMA table_info(", table_name, ")")
        tryCatch({
          col_info <- dbGetQuery(db_connection, query)
          id_columns <- col_info$name[grep("_id$", col_info$name)]  # Get columns ending with `_id`
          
          # Always include patient_id and hospitalization_id if they exist
          if ("patient_id" %in% col_info$name) {
            id_columns <- unique(c(id_columns, "patient_id"))
          }
          if ("hospitalization_id" %in% col_info$name) {
            id_columns <- unique(c(id_columns, "hospitalization_id"))
          }
          
          return(id_columns)
        }, error = function(e) {
          flog.error("Error fetching column info for %s: %s", table_name, e$message)
          return(NULL)
        })
      }
      
      cohort_id_columns <- get_id_columns(cohort_table)
      inclusion_id_columns <- get_id_columns(inclusion_table)
      
      # Find common `_id` column
      common_id_column <- intersect(cohort_id_columns, inclusion_id_columns)
      
      if (length(common_id_column) == 0) {
        flog.warn("No common `_id` column found for joining. Running without join.")
        query <- paste0("SELECT * FROM ", cohort_table, " WHERE ", condition, " LIMIT 5")
      } else {
        # Use the first common `_id` column
        join_column <- common_id_column[1]
        flog.info("Joining tables on column: %s", join_column)
        
        # **Construct SQL query with LEFT JOIN**
        query <- paste0("
        SELECT c.*, i.* 
        FROM ", cohort_table, " AS c
        LEFT JOIN ", inclusion_table, " AS i
        ON c.", join_column, " = i.", join_column, "
        WHERE ", condition, "
        LIMIT 5
      ")
      }
    }
    
    flog.info("Executing query: %s", query)
    
    # **Execute SQL Query and store results**
    tryCatch({
      result <- dbGetQuery(db_connection, query)
      filtered_data(result)  # Store result in reactiveVal
    }, error = function(e) {
      flog.error("Error fetching joined data: %s", e$message)
      filtered_data(NULL)  # Reset if error occurs
    })
  })
  
  # Render stored `filtered_data()` in DataTable
  output$filtered_data_table <- DT::renderDataTable({
    req(filtered_data())
    filtered_data()
  })
  
  
  generate_summary_stats <- function(data) {
    if (is.null(data) || nrow(data) == 0) {
      return(NULL)
    }
    
    # Identify numeric columns only
    numeric_cols <- sapply(data, is.numeric)
    data_numeric <- data[, numeric_cols, drop = FALSE]
    
    if (ncol(data_numeric) == 0) {
      return(data.frame(Message = "No numeric columns available for summary"))
    }
    
    # Compute summary statistics
    summary_stats <- data.frame(
      Metric = c("Count", "Mean", "Std Dev", "Min", "25%", "50%", "75%", "Max")
    )
    
    for (col in colnames(data_numeric)) {
      stats <- c(
        Count = nrow(data_numeric),
        Mean = mean(data_numeric[[col]], na.rm = TRUE),
        Std_Dev = sd(data_numeric[[col]], na.rm = TRUE),
        Min = min(data_numeric[[col]], na.rm = TRUE),
        P25 = quantile(data_numeric[[col]], 0.25, na.rm = TRUE),
        P50 = median(data_numeric[[col]], na.rm = TRUE),
        P75 = quantile(data_numeric[[col]], 0.75, na.rm = TRUE),
        Max = max(data_numeric[[col]], na.rm = TRUE)
      )
      
      summary_stats[[col]] <- stats
    }
    
    return(summary_stats)
  }
  
  summary_data <- reactive({
    req(filtered_data())  # Ensure data exists
    generate_summary_stats(filtered_data())
  })
  
  output$summary_stats_table <- DT::renderDataTable({
    req(summary_data())  # Ensure data exists
    summary_data()
  })
  

  # Close DB connection on exit
  onStop(function() {
    dbDisconnect(db_connection)
  })
}