## 1. Pandas Integration

- [ ] 1.1 Add pandas to dependencies
- [ ] 1.2 Create ResultSetDataFrame converter (result rows → pandas DataFrame)
- [ ] 1.3 Implement column data type preservation
- [ ] 1.4 Handle NULL/None values correctly
- [ ] 1.5 Add tests for DataFrame conversion

## 2. yaml-reference Integration (COMPLETED)

- [x] 2.1 Add yaml-reference to dependencies
- [x] 2.2 Create reference file loader (handle !reference tags)
- [x] 2.3 Implement wildcard reference support (!reference-all)
- [x] 2.4 Support YAML, CSV, and SQL file formats
- [x] 2.5 Implement path resolution (relative to test file or project root)
- [x] 2.6 Add error handling for missing reference files
- [x] 2.7 Add tests for reference loading

## 3. DataFrame Normalization

- [ ] 3.1 Implement column sorting (alphabetical order)
- [ ] 3.2 Implement row sorting (by all columns)
- [ ] 3.3 Create Normalizer class for comparison preparation
- [ ] 3.4 Add tests for normalization scenarios

## 4. rows_equal Expectation Implementation

- [ ] 4.1 Create RowsEqualExpectation class
- [ ] 4.2 Parse expected data from `rows_equal:` section
- [ ] 4.3 Support `rows:` (inline YAML dicts)
- [ ] 4.4 Support `csv:` (inline CSV string)
- [ ] 4.5 Support `sql:` (SELECT statement)
- [ ] 4.6 Support external references via yaml-reference
- [ ] 4.7 Implement expectation evaluation (DataFrame comparison)
- [ ] 4.8 Implement pandas `.assert_frame_equal()` for diffs
- [ ] 4.9 Create failure reporting with clear diff output

## 5. Data Type Handling

- [ ] 5.1 Test string column comparison
- [ ] 5.2 Test numeric column comparison (int, float)
- [ ] 5.3 Test boolean column comparison
- [ ] 5.4 Test NULL/None handling
- [ ] 5.5 Test datetime column comparison
- [ ] 5.6 Test float precision tolerance (using sql-unit.yaml config)

## 6. SQL-Unit Config Extension

- [ ] 6.1 Add float_precision config option to sql-unit.yaml schema
- [ ] 6.2 Load float_precision from config (with sensible default like 1e-10)
- [ ] 6.3 Pass float_precision to comparison logic for float tolerance

## 7. Error Handling and Reporting

- [ ] 7.1 Implement clear diff output on expectation failure
- [ ] 7.2 Show expected vs actual DataFrames side-by-side
- [ ] 7.3 Highlight differences in output
- [ ] 7.4 Include test identification in error messages
- [ ] 7.5 Add file reference path information to errors

## 8. Specs Implementation

- [ ] 8.1 Implement `rows-equal-expectations` spec requirements
- [ ] 8.2 Implement `yaml-reference-support` spec requirements

## 9. Unit and Integration Tests

- [ ] 9.1 Create unit tests for DataFrame conversion
- [ ] 9.2 Create unit tests for reference file loading
- [ ] 9.3 Create tests for column/row normalization
- [ ] 9.4 Create tests for rows_equal expectation (all data sources)
- [ ] 9.5 Create tests for reference wildcards
- [ ] 9.6 Create tests for data type handling
- [ ] 9.7 Create tests for error cases
- [ ] 9.8 Achieve >80% code coverage
