library(tableone)
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
      register_all_tables(uploaded_data())  # Call the function to register all tables
    } else {
      flog.error("No valid data files were uploaded.")
    }
  })
  
  # Function to register all tables in DuckDB
  register_all_tables <- function(uploaded_data) {
    for (file_name in names(uploaded_data)) {
      tryCatch({
        # Determine the table name (remove file extension)
        table_name <- gsub("\\.(csv|parquet)$", "", file_name)
        file_path <- uploaded_data[[file_name]]
        
        # Check if table already exists before registering
        if (!table_name %in% dbListTables(db_connection)) {
          # Register the table in DuckDB
          dbExecute(db_connection, paste0("CREATE OR REPLACE TABLE ", table_name, 
                                         " AS SELECT * FROM read_parquet('", file_path, "')"))
          flog.info("Table %s registered successfully from file %s.", table_name, file_name)
        } else {
          flog.info("Table %s already registered, skipping.", table_name)
        }
      }, error = function(e) {
        flog.error("Error registering table %s: %s", file_name, e$message)
      })
    }
  }
  
  # Initialize inputs to NULL or empty
  observe({
    updateSelectizeInput(session, "cohort_entry_events_1", selected = NULL)
    updateSelectizeInput(session, "cohort_column_selection_1", selected = NULL)
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
                    choices = c("None" = "", table_choices()), selected = "", multiple = FALSE),
        selectizeInput(paste0("cohort_column_selection_", i), "Select Column",
                    choices = c("None" = ""), selected = "", multiple = FALSE),
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
                    choices = c("None" = "", table_choices()), selected = "", multiple = FALSE),
        selectizeInput(paste0("inclusion_column_selection_", i), "Select Column",
                    choices = c("None" = ""), selected = "", multiple = FALSE),
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
                    choices = c("None" = "", table_choices()), selected = "", multiple = FALSE),
        selectizeInput(paste0("exclusion_column_selection_", i), "Select Column",
                    choices = c("None" = ""), selected = "", multiple = FALSE),
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
          current_i <- i
          
          observeEvent(input[[paste0(column_prefix, current_i)]], {
            req(input[[paste0(column_prefix, current_i)]])
            
            invalidateLater(1000, session)

            selected_column <- input[[paste0(column_prefix, current_i)]]
            selected_table <- input[[paste0(event_prefix, current_i)]]
            
            # Ensure we are using the full table path
            full_file_names <- names(uploaded_data())
            cleaned_names <- gsub("\\.(csv|parquet)$", "", full_file_names, ignore.case = TRUE)
            selected_table_full <- full_file_names[which(cleaned_names == selected_table)]
            
            # **Fetch Column Type**
            type_query <- paste0("PRAGMA table_info(", selected_table, ")")
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
                    FROM ", selected_table, "
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
                    FROM ", selected_table, "
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
  
  # Add a reactiveVal to store the filtered data
  filtered_data <- reactiveVal(NULL)
  
  # Remove the automatic observe block that updates filtered_data
  # Instead, create a function to build the query
  build_cohort_query <- function() {
    req(uploaded_data())
    
    num_criteria <- cohort_criteria_count()
    if (num_criteria < 1) return(NULL)
    
    # Get selected tables and columns
    cohort_table <- input[[paste0("cohort_entry_events_", 1)]]
    cohort_column <- input[[paste0("cohort_column_selection_", 1)]]
    cohort_filter <- input[[paste0("cohort_dynamic_filter_ui_", 1)]]
    
    inclusion_table <- input[[paste0("inclusion_criteria_events_", 1)]]
    inclusion_column <- input[[paste0("inclusion_column_selection_", 1)]]
    inclusion_filter <- input[[paste0("inclusion_dynamic_filter_ui_", 1)]]
    
    exclusion_table <- input[[paste0("exclusion_criteria_events_", 1)]]
    exclusion_column <- input[[paste0("exclusion_column_selection_", 1)]]
    exclusion_filter <- input[[paste0("exclusion_dynamic_filter_ui_", 1)]]
    
    # Basic validation
    if (is.null(cohort_table) || cohort_table == "" || 
        is.null(cohort_column) || cohort_column == "" || 
        is.null(cohort_filter)) {
      return(NULL)
    }
    
    # Function to get common ID columns between two tables
    get_common_id_columns <- function(table1, table2) {
      query1 <- paste0("PRAGMA table_info(", table1, ")")
      query2 <- paste0("PRAGMA table_info(", table2, ")")
      
      tryCatch({
        col_info1 <- dbGetQuery(db_connection, query1)
        col_info2 <- dbGetQuery(db_connection, query2)
        
        # Get all ID columns (including patient_id and hospitalization_id)
        id_columns1 <- col_info1$name[grep("_id$", col_info1$name)]
        id_columns2 <- col_info2$name[grep("_id$", col_info2$name)]
        
        # Always include patient_id and hospitalization_id if they exist
        if ("patient_id" %in% col_info1$name) id_columns1 <- unique(c(id_columns1, "patient_id"))
        if ("hospitalization_id" %in% col_info1$name) id_columns1 <- unique(c(id_columns1, "hospitalization_id"))
        if ("patient_id" %in% col_info2$name) id_columns2 <- unique(c(id_columns2, "patient_id"))
        if ("hospitalization_id" %in% col_info2$name) id_columns2 <- unique(c(id_columns2, "hospitalization_id"))
        
        common_columns <- intersect(id_columns1, id_columns2)
        flog.info("Common ID columns between %s and %s: %s", table1, table2, toString(common_columns))
        return(common_columns)
      }, error = function(e) {
        flog.error("Error getting common ID columns: %s", e$message)
        return(NULL)
      })
    }
    
    # Start with base query
    query <- paste0("SELECT * FROM ", cohort_table, " AS c")
    
    # Add LEFT JOIN for inclusion if different from cohort
    if (!is.null(inclusion_table) && inclusion_table != "" && inclusion_table != cohort_table) {
      common_columns <- get_common_id_columns(cohort_table, inclusion_table)
      if (length(common_columns) > 0) {
        join_column <- common_columns[1]  # Use the first common column
        query <- paste0(query, "
          LEFT JOIN ", inclusion_table, " AS i
          ON c.", join_column, " = i.", join_column)
      }
    }
    
    # Add LEFT JOIN for exclusion if different from both cohort and inclusion
    if (!is.null(exclusion_table) && exclusion_table != "" && 
        exclusion_table != cohort_table && exclusion_table != inclusion_table) {
      # Try to join with cohort table first
      common_columns <- get_common_id_columns(cohort_table, exclusion_table)
      if (length(common_columns) > 0) {
        join_column <- common_columns[1]
        query <- paste0(query, "
          LEFT JOIN ", exclusion_table, " AS e
          ON c.", join_column, " = e.", join_column)
      } else {
        # If no common columns with cohort, try inclusion table
        common_columns <- get_common_id_columns(inclusion_table, exclusion_table)
        if (length(common_columns) > 0) {
          join_column <- common_columns[1]
          query <- paste0(query, "
            LEFT JOIN ", exclusion_table, " AS e
            ON i.", join_column, " = e.", join_column)
        }
      }
    }
    
    # Build WHERE conditions
    where_conditions <- c()
    
    # Cohort condition
    if (is.numeric(cohort_filter)) {
      where_conditions <- c(where_conditions, 
        paste0("c.", cohort_column, " BETWEEN ", cohort_filter[1], " AND ", cohort_filter[2]))
    } else if (is.character(cohort_filter)) {
      where_conditions <- c(where_conditions,
        paste0("c.", cohort_column, " IN ('", paste(cohort_filter, collapse = "','"), "')"))
    }
    
    # Inclusion condition
    if (!is.null(inclusion_filter)) {
      if (inclusion_table == cohort_table) {
        # If inclusion is same as cohort, use 'c' alias
        if (is.numeric(inclusion_filter)) {
          where_conditions <- c(where_conditions,
            paste0("c.", inclusion_column, " BETWEEN ", inclusion_filter[1], " AND ", inclusion_filter[2]))
        } else if (is.character(inclusion_filter)) {
          where_conditions <- c(where_conditions,
            paste0("c.", inclusion_column, " IN ('", paste(inclusion_filter, collapse = "','"), "')"))
        }
      } else {
        # If inclusion is different table, use 'i' alias
        if (is.numeric(inclusion_filter)) {
          where_conditions <- c(where_conditions,
            paste0("i.", inclusion_column, " BETWEEN ", inclusion_filter[1], " AND ", inclusion_filter[2]))
        } else if (is.character(inclusion_filter)) {
          where_conditions <- c(where_conditions,
            paste0("i.", inclusion_column, " IN ('", paste(inclusion_filter, collapse = "','"), "')"))
        }
      }
    }
    
    # Exclusion condition
    if (!is.null(exclusion_filter)) {
      if (exclusion_table == cohort_table) {
        # If exclusion is same as cohort, use 'c' alias
        if (is.numeric(exclusion_filter)) {
          where_conditions <- c(where_conditions,
            paste0("c.", exclusion_column, " NOT BETWEEN ", exclusion_filter[1], " AND ", exclusion_filter[2]))
        } else if (is.character(exclusion_filter)) {
          where_conditions <- c(where_conditions,
            paste0("c.", exclusion_column, " NOT IN ('", paste(exclusion_filter, collapse = "','"), "')"))
        }
      } else if (exclusion_table == inclusion_table) {
        # If exclusion is same as inclusion, use 'i' alias
        if (is.numeric(exclusion_filter)) {
          where_conditions <- c(where_conditions,
            paste0("i.", exclusion_column, " NOT BETWEEN ", exclusion_filter[1], " AND ", exclusion_filter[2]))
        } else if (is.character(exclusion_filter)) {
          where_conditions <- c(where_conditions,
            paste0("i.", exclusion_column, " NOT IN ('", paste(exclusion_filter, collapse = "','"), "')"))
        }
      } else {
        # If exclusion is different table, use 'e' alias
        if (is.numeric(exclusion_filter)) {
          where_conditions <- c(where_conditions,
            paste0("e.", exclusion_column, " NOT BETWEEN ", exclusion_filter[1], " AND ", exclusion_filter[2]))
        } else if (is.character(exclusion_filter)) {
          where_conditions <- c(where_conditions,
            paste0("e.", exclusion_column, " NOT IN ('", paste(exclusion_filter, collapse = "','"), "')"))
        }
      }
    }
    
    # Add WHERE clause if we have conditions
    if (length(where_conditions) > 0) {
      query <- paste0(query, "\nWHERE ", paste(where_conditions, collapse = " AND "))
    }
    
    return(query)
  }
  
  # Modify the Generate Summary button handler
  observeEvent(input$generate_summary, {
    req(uploaded_data())  # Ensure data is uploaded
    
    # Build the query
    query <- build_cohort_query()
    if (is.null(query)) {
      showNotification("Please select cohort criteria before generating summary.", type = "warning")
      return(NULL)
    }
    
    flog.info("Executing query: %s", query)
    
    # Execute query and store results
    tryCatch({
      result <- dbGetQuery(db_connection, query)
      filtered_data(result)  # Store result in reactiveVal
      
      # Generate summary statistics
      summary_stats <- generate_summary_stats(result)
      summary_data(summary_stats)  # Store summary data
      
      # Display summary statistics in a DataTable
      output$summary_stats_table <- DT::renderDataTable({
        req(summary_data())
        summary_data()
      })
    }, error = function(e) {
      flog.error("Error executing query: %s", e$message)
      showNotification("Error generating summary. Please check your criteria.", type = "error")
    })
  })
  
  # Update the filtered data table output
  output$filtered_data_table <- DT::renderDataTable({
    req(filtered_data())  # Ensure filtered_data() is available
    DT::datatable(filtered_data(), options = list(pageLength = 3))
  })
  
  generate_summary_stats <- function(data) {
    if (is.null(data) || nrow(data) == 0) {
      flog.warn("No data available for summary generation.")
      return(NULL)
    }
    
    # Identify numeric and categorical columns
    numeric_cols <- sapply(data, is.numeric)
    categorical_cols <- sapply(data, is.factor) | sapply(data, is.character)
    
    # Combine numeric and categorical columns
    all_cols <- colnames(data)[numeric_cols | categorical_cols]
    
    # Exclude patient_id and hospitalization_id from summary columns
    all_cols <- setdiff(all_cols, c("patient_id", "hospitalization_id", "zipcode_five_digit", "zipcode_nine_digit", "census_block_group", "latitude", "longitude"))
    
    if (length(all_cols) == 0) {
      flog.warn("No numeric or categorical columns available for summary.")
      return(data.frame(Message = "No numeric or categorical columns available for summary"))
    }
    
    # Create a TableOne object
    table_one <- CreateTableOne(vars = all_cols, data = data, test = TRUE)
    
    # Convert TableOne to a data frame for rendering
    summary_stats <- print(table_one, printToggle = FALSE, quote = FALSE)
    
    flog.info("Summary statistics generation completed.")
    return(summary_stats)
  }
  
  # Add a reactiveVal to store summary data
  summary_data <- reactiveVal(NULL)
  
  # Handle the export of filtered data
  output$export_data <- downloadHandler(
    filename = function() {
      paste("exported_data_", Sys.Date(), ".csv", sep = "")
    },
    content = function(file) {
      req(filtered_data())  # Ensure filtered_data is available
      
      # Select only the relevant columns (hospitalization_id, patient_id)
      export_data <- filtered_data()[, c("hospitalization_id", "patient_id"), drop = FALSE]
      
      # Remove rows with all NA values
      export_data <- na.omit(export_data)
      
      # Check if export_data is empty
      if (nrow(export_data) == 0) {
        # Optionally, you can stop the function and provide feedback
        stop("No data available to export. Please ensure that either hospitalization_id or patient_id exists.")
      }
      
      # Write the data to a CSV file
      write.csv(export_data, file, row.names = FALSE)
    }
  )
  
  # Close DB connection on exit
  onStop(function() {
    dbDisconnect(db_connection)
  })
}