Feature: A user can associate datasets with assets 
        Scenario: Add an external dataset to a new table asset
                Given an admin creates the User "test_user@fakedomain.com"
                Given the user "test_user@fakedomain.com" is logged in
                Given the user navigates to "/build/"
                Given the user clicks the "Sandbox" link
                Given the user inputs "Test story" for the "title" field 
                Given the user inputs "Test User" for the "byline" field 
                Given the user inputs "My summary, so exciting!" for the "summary" textarea 
                Given the user clicks on "Untitled Section" in the section list
                Given the user clicks the "Table" icon in the "center" container
                Given the user inputs "https://docs.google.com/spreadsheet/pub?key=0AvaXS4x_XvJmdGthMFBSb1BJOUNPTnhaNWN4UDZnZkE&output=html" in the "Enter table URL" input
                Given the user clicks the "Save Changes" button
                Given the user clicks on the "Data Sources" link 
                Given the user clicks on the "Add Dataset" button
                Given the user inputs "FOIA No Heats 2011 to Present" in the "Data set name" input
                Given the user inputs "City of Chicago" in the "Source" input
                Given the user inputs "https://docs.google.com/spreadsheet/ccc?key=0AvaXS4x_XvJmdGthMFBSb1BJOUNPTnhaNWN4UDZnZkE#gid=0" in the "Data URL" input
                Given the user clicks the "Save" button
                Then "FOIA No Heats 2011 to Present" appears in the dataset list below the asset content
                Then "FOIA No Heats 2011 to Present" has an "external" icon
                Then "FOIA No Heats 2011 to Present" lists "City of Chicago" as the source
                Given the user refreshes the browser
                Given the user clicks on "Untitled Section" in the section list
                Given the user clicks on the "Data Sources" link 
                Then "FOIA No Heats 2011 to Present" appears in the dataset list


        Scenario: Add an uploaded CSV file dataset to a new table asset
                Given an admin creates the User "test_user@fakedomain.com"
                Given the user "test_user@fakedomain.com" is logged in
                Given the user navigates to "/build/"
                Given the user clicks the "Sandbox" link
                Given the user inputs "Test story" for the "title" field 
                Given the user inputs "Test User" for the "byline" field 
                Given the user inputs "My summary, so exciting!" for the "summary" textarea 
                Given the user clicks on "Untitled Section" in the section list
                Given the user clicks the "Table" icon in the "center" container
                Given the user inputs "https://docs.google.com/spreadsheet/pub?key=0AvaXS4x_XvJmdGthMFBSb1BJOUNPTnhaNWN4UDZnZkE&output=html" in the "Enter table URL" input
                Given the user clicks the "Save Changes" button
                Given the user clicks on the "Data Sources" link
                Given the user clicks on the "Add Dataset" button
                Given the user inputs "Test CSV Data" in the "Data set name" input
                Given the user inputs "City of Chicago" in the "Source" input
                Given the user clicks the "choose file" button
                Given the user selects the file "test_data.csv"
                Given the user clicks the "Save" button
                Then "Test CSV Data" appears in the dataset list below the asset content
                Then "Test CSV Data" has a "download" icon
                Then "Test CSV Data" lists "City of Chicago" as the source
                Given the user refreshes the browser
                Given the user clicks on "Untitled Section" in the section list
                
                Given the user clicks on the "Data Sources" link
                Then "Test CSV Data" appears in the dataset list


        Scenario: Add a dataset to an existing table asset
                Given an admin creates the User "test_user@fakedomain.com"
                Given the user "test_user@fakedomain.com" is logged in
                Given the user navigates to "/build/"
                Given the user clicks the "Sandbox" link
                Given the user inputs "Test story" for the "title" field 
                Given the user inputs "Test User" for the "byline" field 
                Given the user inputs "My summary, so exciting!" for the "summary" textarea 
                Given the user clicks on "Untitled Section" in the section list
                Given the user clicks the "Table" icon in the "center" container
                Given the user inputs "https://docs.google.com/spreadsheet/pub?key=0AvaXS4x_XvJmdGthMFBSb1BJOUNPTnhaNWN4UDZnZkE&output=html" in the "Enter table URL" input
                Given the user clicks the "Save Changes" button
                Given the user refreshes the browser
                Given the user clicks on "Untitled Section" in the section list
                Given the user clicks on the "Data Sources" link
                Given the user clicks on the "Add Dataset" button
                Given the user inputs "FOIA No Heats 2011 to Present" in the "Data set name" input
                Given the user inputs "City of Chicago" in the "Source" input
                Given the user inputs "https://docs.google.com/spreadsheet/ccc?key=0AvaXS4x_XvJmdGthMFBSb1BJOUNPTnhaNWN4UDZnZkE#gid=0" in the "Data URL" input
                Given the user clicks the "Save" button
                Then "FOIA No Heats 2011 to Present" appears in the dataset list
                Given the user refreshes the browser
                Given the user clicks on "Untitled Section" in the section list
                Then "FOIA No Heats 2011 to Present" appears in the dataset list below the asset content
                Then "FOIA No Heats 2011 to Present" has an "external" icon
                Then "FOIA No Heats 2011 to Present" lists "City of Chicago" as the source

        Scenario: Add multiple datasets to an existing table asset
                Given an admin creates the User "test_user@fakedomain.com"
                Given the user "test_user@fakedomain.com" is logged in
                Given the user navigates to "/build/"
                Given the user clicks the "Sandbox" link
                Given the user inputs "Test story for adding multiple datasets" for the "title" field 
                Given the user inputs "Test User" for the "byline" field 
                Given the user inputs "My summary, so exciting!" for the "summary" textarea 
                Given the user clicks on "Untitled Section" in the section list
                Given the user clicks the "Table" icon in the "center" container
                Given the user inputs "https://docs.google.com/spreadsheet/pub?key=0AvaXS4x_XvJmdGthMFBSb1BJOUNPTnhaNWN4UDZnZkE&output=html" in the "Enter table URL" input
                Given the user clicks the "Save Changes" button
                Given the user clicks on "Untitled Section" in the section list
                Given the user clicks on the "Data Sources" link
                Given the user clicks on the "Add Dataset" button
                Given the user inputs "FOIA No Heats 2011 to Present" in the "Data set name" input
                Given the user inputs "City of Chicago" in the "Source" input
                Given the user inputs "https://docs.google.com/spreadsheet/ccc?key=0AvaXS4x_XvJmdGthMFBSb1BJOUNPTnhaNWN4UDZnZkE#gid=0" in the "Data URL" input
                Given the user clicks the "Save and Add Another" button
                Given the user inputs "2010-2011 Colorado School CSAP Summary" in the "Data set name" input
                Given the user inputs "CDE" in the "Source" input
                Given the user inputs "http://codataengine.org/find/2010-2011-colorado-school-csap-summary" in the "Data URL" input
                Given the user clicks the "Save" button
                Then "FOIA No Heats 2011 to Present" appears in the dataset list below the asset content
                Then "FOIA No Heats 2011 to Present" has an "external" icon
                Then "FOIA No Heats 2011 to Present" lists "City of Chicago" as the source
                Then "2010-2011 Colorado School CSAP Summary" appears in the dataset list below the asset content
                Then "2010-2011 Colorado School CSAP Summary" has an "external" icon
                Then "2010-2011 Colorado School CSAP Summary" lists "CDE" as the source

        Scenario: Add an additional dataset to a table asset
                Given the scenario "Add an external dataset to a new table asset" has been run
                Given the user clicks on the "Add Dataset" button
                Given the user inputs "Test CSV Data" in the "Data set name" input
                Given the user inputs "City of Chicago" in the "Source" input
                Given the user clicks the "choose file" button
                Given the user selects the file "test_data.csv"
                Given the user clicks the "Save" button
                Then "FOIA No Heats 2011 to Present" appears in the dataset list below the asset content
                Then "FOIA No Heats 2011 to Present" has an "external" icon
                Then "FOIA No Heats 2011 to Present" lists "City of Chicago" as the source
                Then "Test CSV Data" appears in the dataset list below the asset content
                Then "Test CSV Data" has a "download" icon
                Then "Test CSV Data" lists "City of Chicago" as the source
                Given the user refreshes the browser
                Given the user clicks on "Untitled Section" in the section list
                Given the user clicks on the "Data Sources" link
                Then "Test CSV Data" appears in the dataset list
                Then "FOIA No Heats 2011 to Present" appears in the dataset list

        Scenario: Add an additional dataset to a table asset after re-adding it to a section 
                Given the scenario "Add an external dataset to a new table asset" has been run
                Given the user clicks the "Close" button
                
                Given the user clicks the "Remove" link for asset in the "center" container
                Given the user opens the asset drawer
                Given the user drags the asset "https://docs.google.com/spreadsheet/pub?key=0AvaXS4x_XvJmdGthMFBSb1BJOUNPTnhaNWN4UDZnZkE&output=html" from the asset drawer to the "center" container 
                
                Given the user clicks on the "Data Sources" link
                Then "FOIA No Heats 2011 to Present" appears in the dataset list
                Given the user clicks on the "Add Dataset" button
                Given the user inputs "Test CSV Data" in the "Data set name" input
                Given the user clicks the "choose file" button
                Given the user selects the file "test_data.csv"
                Given the user clicks the "Save" button
                Then "FOIA No Heats 2011 to Present" appears in the dataset list below the asset content
                Then "FOIA No Heats 2011 to Present" has an "external" icon
                Then "FOIA No Heats 2011 to Present" lists "City of Chicago" as the source
                Then "Test CSV Data" appears in the dataset list below the asset content
                Then "Test CSV Data" has a "download" icon
                Then "Test CSV Data" lists "City of Chicago" as the source
                Given the user refreshes the browser
                Given the user clicks on "Untitled Section" in the section list
                Then "FOIA No Heats 2011 to Present" appears in the dataset list below the asset content
                Then "FOIA No Heats 2011 to Present" has an "external" icon
                Then "FOIA No Heats 2011 to Present" lists "City of Chicago" as the source
                Then "Test CSV Data" appears in the dataset list below the asset content
                Then "Test CSV Data" has a "download" icon
                Then "Test CSV Data" lists "City of Chicago" as the source
                Given the user clicks on the "Data Sources" link
                Then "Test CSV Data" appears in the dataset list
                Then "FOIA No Heats 2011 to Present" appears in the dataset list

        Scenario: Add an external dataset to a table asset after re-adding it to a section
                Given the scenario "Add an external dataset to a new table asset" has been run
                Given the user clicks the "Close" button
                Given the user clicks the "Remove" link for asset in the "center" container
                Given the user clicks the "Table" icon in the "center" container
                Given the user enters the following in the "Or, paste the embed code for the table" field:
                """
                <table>
                  <tr>
                    <th>Col 1</th>
                    <th>Col 2</th>
                  </tr>
                  <tr>
                    <td>Blah</td>
                    <td>20.231</td>
                  </tr>
                </table>
                """
                Given the user clicks the "Save Changes" button
                Given the user clicks on the "Data Sources" link
                Then no datasets should be listed
                Given the user clicks the "Close" button
                Given the user clicks the "Remove" link for asset in the "center" container
                Given the user opens the asset drawer
                Given the user drags the last removed asset from the asset drawer to the "center" container
                Given the user clicks on the "Data Sources" link
                Then no datasets should be listed
                Given the user clicks on the "Add Dataset" button
                Given the user inputs "2010-2011 Colorado School CSAP Summary" in the "Data set name" input
                Given the user inputs "CDE" in the "Source" input
                Given the user inputs "http://codataengine.org/find/2010-2011-colorado-school-csap-summary" in the "Data URL" input
                Given the user clicks the "Save" button
                Then "2010-2011 Colorado School CSAP Summary" appears in the dataset list below the asset content
                Then "2010-2011 Colorado School CSAP Summary" has an "external" icon
                Then "2010-2011 Colorado School CSAP Summary" lists "CDE" as the source

        Scenario: Add an additional dataset to a table asset after the layout has been changed
                Given the scenario "Add an external dataset to a new table asset" has been run
                Given the user clicks the "Close" button
                Given the user changes the layout to "Side by Side"
                Given the user opens the asset drawer
                Given the user drags the asset "https://docs.google.com/spreadsheet/pub?key=0AvaXS4x_XvJmdGthMFBSb1BJOUNPTnhaNWN4UDZnZkE&output=html" from the asset drawer to the "left" container 
                Given the user clicks on the "Data Sources" link
                Then "FOIA No Heats 2011 to Present" appears in the dataset list
                Given the user clicks on the "Add Dataset" button
                Given the user inputs "2010-2011 Colorado School CSAP Summary" in the "Data set name" input
                Given the user inputs "CDE" in the "Source" input
                Given the user inputs "http://codataengine.org/find/2010-2011-colorado-school-csap-summary" in the "Data URL" input
                Given the user clicks the "Save" button
                Then "FOIA No Heats 2011 to Present" appears in the dataset list below the asset content
                Then "FOIA No Heats 2011 to Present" has an "external" icon
                Then "FOIA No Heats 2011 to Present" lists "City of Chicago" as the source
                Then "2010-2011 Colorado School CSAP Summary" appears in the dataset list below the asset content
                Then "2010-2011 Colorado School CSAP Summary" has an "external" icon
                Then "2010-2011 Colorado School CSAP Summary" lists "CDE" as the source

        Scenario: View datasets in the story viewer
                Given the scenario "Add an additional dataset to a table asset" has been run
                Given the user clicks the "Preview" link
                Given the user clicks the "Next" button
                Then "FOIA No Heats 2011 to Present" appears in the dataset list below the asset content
                Then "FOIA No Heats 2011 to Present" has an "external" icon
                Then "FOIA No Heats 2011 to Present" lists "City of Chicago" as the source
                Then "Test CSV Data" appears in the dataset list below the asset content
                Then "Test CSV Data" has a "download" icon
                Then "Test CSV Data" lists "City of Chicago" as the source
                Given the user clicks the "FOIA No Heats 2011 to Present" link
                Then the URL "https://docs.google.com/spreadsheet/ccc?key=0AvaXS4x_XvJmdGthMFBSb1BJOUNPTnhaNWN4UDZnZkE#gid=0" opens in a new tab
                Given the user closes the browser tab
                Given the user clicks the "Test CSV Data" link
                Then the user is prompted to download the file "test_data.csv"

        Scenario: View datasets on the story detail page             
                Given the scenario "Add an additional dataset to a table asset" has been run
                Given the user navigates to the story detail page for the story "Test story"
                Given the user clicks the "Get the Data" button
                Then "FOIA No Heats 2011 to Present" appears in the dataset dropdown list

                Then "FOIA No Heats 2011 to Present" has an "external" icon
                Then "FOIA No Heats 2011 to Present" lists "City of Chicago" as the source
                Then "Test CSV Data" appears in the dataset dropdown list
                Then "Test CSV Data" has a "download" icon
                Then "Test CSV Data" lists "City of Chicago" as the source
                Given the user clicks the "FOIA No Heats 2011 to Present" link
                Then the URL "https://docs.google.com/spreadsheet/ccc?key=0AvaXS4x_XvJmdGthMFBSb1BJOUNPTnhaNWN4UDZnZkE#gid=0" opens in a new tab
                Given the user closes the browser tab
                Given the user clicks the "Test CSV Data" link
                Then the user is prompted to download the file "test_data.csv"

        Scenario: Remove a dataset from an asset
                Given the scenario "Add an additional dataset to a table asset" has been run
                Given the user clicks the "Remove" button for the dataset "FOIA No Heats 2011 to Present"
                Then "FOIA No Heats 2011 to Present" does not appear in the dataset list
                Then "Test CSV Data" appears in the dataset list
                Given the user clicks the "Preview" link
                Given the user clicks the "Next" button
                Then "FOIA No Heats 2011 to Present" does not appear in the dataset list below the asset content
                Then "Test CSV Data" appears in the dataset list below the asset content
                Given the user navigates to the story detail page for the story "Test story"
                Given the user clicks the "Get the Data" button
                Then "FOIA No Heats 2011 to Present" does not appear in the dataset dropdown list
                Then "Test CSV Data" appears in the dataset dropdown list
