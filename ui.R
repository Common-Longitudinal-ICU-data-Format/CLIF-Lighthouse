ui <- fluidPage(
  fluidRow(
    column(4, offset = 4,
           titlePanel("CLIF Cohort Discovery"))
  ),

  # Centering File Input
  fluidRow(
    column(4, offset = 4,  # Centering within a 12-column layout
           fileInput("main", "Select one or more files", multiple = TRUE,
                     accept = c(".csv", ".parquet", ".fst"))
    )
  ),

  # Conditional Panel: Display only if files are uploaded
  conditionalPanel(
    condition = "output.filesUploaded == true",

    # Tabs for organizing UI
    tabsetPanel(
      tabPanel("Cohort Entry",
               fluidRow(
                 column(12,
                        wellPanel(
                          tags$h4("Define Cohort Entry Event"),
                          textAreaInput("cohort_definition",
                                        label = NULL,
                                        placeholder = "Enter your cohort definition here...",
                                        rows = 3),
                          actionButton("save_definition", "Save Definition")
                        )
                 )
               ),

               hr(),
               fluidRow(
                 column(4,
                        wellPanel(
                          tags$h4("Cohort Entry Events"),
                          uiOutput("cohort_entry_ui"),  # Dynamically generate multiple criteria inputs here
                          actionButton("add_criteria", "+ Add Cohort Entry Event"),
                          actionButton("remove_criteria", "- Remove Last Cohort Entry", class = "btn-warning")
                        )
                 ),

                 column(4,
                        wellPanel(
                          tags$h4("Inclusion Criteria"),
                          uiOutput("inclusion_criteria_ui"),  # Dynamically generate inclusion criteria inputs
                          actionButton("add_inclusion_criteria", "+ Add Inclusion Criteria"),
                          actionButton("remove_criteria", "- Remove Last Inclusion Criteria", class = "btn-warning")
                        )
                 ),

                 column(4,
                        wellPanel(
                          tags$h4("Exclusion Criteria"),
                          uiOutput("exclusion_criteria_ui"),  # Dynamically generate exclusion criteria inputs
                          actionButton("add_exclusion_criteria", "+ Add Exclusion Criteria"),
                          actionButton("remove_criteria", "- Remove Last Exclusion Criteria", class = "btn-warning")
                        )
                 )
               ),
               fluidRow(
                 column(12,
                        wellPanel(
                          tags$h4("Cohort Entry Summary"),
                          uiOutput("cohort_entry_summary")  # Display summary of cohort entry events
                        )
                 )
               ),
               fluidRow(
                column(12,
                       wellPanel(
                         tags$h4("Inclusion Criteria Summary"),
                         uiOutput("inclusion_criteria_summary")
                       )
                )
              ),
              fluidRow(
                column(12,
                     wellPanel(
                         tags$h4("Exclusion Criteria Summary"),
                         uiOutput("exclusion_criteria_summary")
                       )
                )
              )
               ),
      tabPanel("Summary",
               tags$h3("Cohort Summary"),
               tags$h5("Cohort Definition"),
               textOutput("cohort_definition_display"),  # Display cohort definition
               tags$h5("Cohort Preview"),
               DT::dataTableOutput("filtered_data_table"),  # Show joined data
               tags$h5("Summary Statistics"),
               DT::dataTableOutput("summary_stats_table")
              ),

      tabPanel("Export",
                tags$h4("Placeholder for future content")  # Empty tab
              ))))
