# Everything LINZ gives that bears on land (4 November 2026)

Arthur, 4 November 2026 (ruling 142): "Get LINZ and all available information and put it all in the database. Always
do this. we want everything." Counts only: no title number, name or address is written here.

## The catalogue

One request for the LINZ Data Service's WFS capabilities (`GetCapabilities`, with our key, through the fetch gate; 3.1
MB) lists **1,856 layers and tables**. The capabilities list only what our key may read: the restricted national
valuation roll (table 113969, "for government organisations only") is named in an abstract and is not listed. Each
entry's abstract states its licence: 1,841 CC BY 4.0, 12 the LINZ Licence for Personal Data 2.3, 3 unstated or
"Creative Commons Attribution". Update cadence is stated in only 7 abstracts ("updated weekly" for the NZ Properties
tables); the LINZ property and boundary data is refreshed weekly, the Full Landonline Dataset with it.

By the catalogue's own keywords the 1,856 are mostly maps of the physical land and sea, not land held or bounded:
Topographic 651, Hydrographic & Maritime 534 (charts, markers, marine features), Aerial Photos 336, NZ Topo 50 199,
Pacific Islands Topo 169, Elevation 117, Landcover 88. These are not taken (no title, parcel, owner, address, property
or survey record in them); a layer of them is one line in `registers/linz/catalogue.py` to add.

The **222** that bear on land were selected by keyword (Property Ownership & Boundaries, Full Landonline Dataset,
LAND-Cadastre, LAND-Ownership, NZ Properties, valuation, Survey, Parcels, Titles & Owners, Roads and Addresses, Crown
Property, Suburbs and Localities, Gazetteer, Land Administrative Areas, Building Outlines), then counted one at a time
(`resultType=hits`, 222 requests about 3 s apart, 08:47 to 09:00 NZDT) and their columns read in one
`DescribeFeatureType`. Every request answered 200; no host was held.

| Tranche | Sources | Rows | Refresh |
| --- | --- | --- | --- |
| 1: the title spine, the parcels and the title-parcel association | 8 | 28,372,507 | weekly |
| 2: titles, estates, memorials, properties and valuation, Crown land, places, roads, buildings | 58 | 64,298,728 | weekly |
| 3: the Full Landonline Dataset, the titles' own shapes | 51 | 329,759,521 | monthly |
| 4: the survey's measurements (observations, setups, marks, vectors, nodes, coordinates, adjustments) | 55 | 639,399,178 | quarterly |
| **taken** | **172** | **1,061,829,934** | |
| not taken (geodetic grids, tile indexes, imagery indexes, tide stations, railway lines, subsets of a held layer, joins of two held ones) | 51 | 28,616,743 | |

At 10,000 rows a page that is about 106,000 pages; the spine's pulls of 3 November ran 1,163 pages in 33 minutes, so
the first pass of everything is some 50 hours of off-peak reading, about nine nights of the capture's six hours, the
smallest tranches first. After it, a week's refreshes are about 9,500 pages (tranches 1 and 2 weekly, 3 monthly, 4
quarterly), about 5 hours a week.

Every taken source other than the five typed ones is read **whole**: no `propertyName`, so every attribute and its
geometry (GeoJSON, longitude and latitude in NZGD2000, EPSG:4167), into its own table in `linz_private`
(`load.whole_sql`: `fid`, `props` as JSON, `geom_type`, `geom`, `xmin` … `ymax`). The addresses (layer 123113) are read
whole from now, so each carries its point. Pages are sorted on the source's id, or for a table with none on its
`audit_id` (unique a row in Landonline), and a row is keyed by that id or, failing one, the service's own feature id.

## Every source

Rows are WFS `numberMatched` on 4 November 2026. Cadence is what the abstract states. Status: held, next (the night's
capture takes it in tranche order), or not taken and why.

| Id | Title | Lane name | Rows | Licence | Geometry | Cadence stated | Tranche | Status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| table 115638 | NZ Properties: Property-Address Reference | `property_addresses` | 6,708,160 | CC BY 4.0 | - | weekly | 1 weekly | held (private) |
| table 51564 | NZ Property Titles Owners List | `owners` | 5,745,217 | Personal Data 2.3 | - | - | 1 weekly | held (typed) |
| layer 51571 | NZ Parcels | `parcels` | 5,500,688 | CC BY 4.0 | yes | - | 1 weekly | next (with its geometry) |
| table 51569 | NZ Title Parcel Association List | `title_parcel_association_list` | 3,000,734 | CC BY 4.0 | - | - | 1 weekly | next (aspatial) |
| table 113970 | NZ Properties: Property-Title Reference | `property_titles` | 2,470,714 | CC BY 4.0 | - | weekly | 1 weekly | held (private) |
| layer 50804 | NZ Property Titles | `titles` | 2,457,581 | CC BY 4.0 | yes | - | 1 weekly | held (attributes; typed) |
| layer 123113 | NZ Addresses | `addresses` | 2,434,677 | CC BY 4.0 | yes | weekly | 1 weekly | held (attributes); next: whole, with its point |
| layer 51681 | NZ Place Names (NZGB) | `place_names` | 54,736 | CC BY 4.0 | yes | - | 1 weekly | held (typed) |
| table 51695 | NZ Title Memorials List (including Mortgages, Leases, Easements) | `title_memorials_list` | 33,006,737 | Personal Data 2.3 | - | - | 2 weekly | next (aspatial) |
| table 51568 | NZ Survey Affected Parcels List | `survey_affected_parcels_list` | 5,326,645 | CC BY 4.0 | - | - | 2 weekly | next (aspatial) |
| table 119620 | NZ Properties: Property-Building Reference | `properties_property_building_reference` | 5,029,306 | CC BY 4.0 | - | weekly | 2 weekly | next (aspatial) |
| layer 101290 | NZ Building Outlines | `building_outlines` | 3,236,141 | CC BY 4.0 | yes | - | 2 weekly | next (with its geometry) |
| table 51566 | NZ Property Title Estates List | `property_title_estates_list` | 2,816,505 | CC BY 4.0 | - | - | 2 weekly | next (aspatial) |
| layer 122657 | NZ Property Boundaries | `property_boundaries` | 2,718,553 | CC BY 4.0 | yes | weekly | 2 weekly | next (with its geometry) |
| table 51567 | NZ Property Titles List | `property_titles_list` | 2,457,581 | CC BY 4.0 | - | - | 2 weekly | next (aspatial) |
| table 113961 | NZ Properties: Perspective | `properties_perspective` | 2,359,093 | CC BY 4.0 | - | weekly | 2 weekly | next (aspatial) |
| layer 113968 | NZ Properties: Unit of Property | `properties_unit_of_property` | 2,359,093 | CC BY 4.0 | yes | weekly | 2 weekly | next (with its geometry) |
| table 51696 | NZ Title Memorials Additional Text List | `title_memorials_additional_text_list` | 1,792,710 | Personal Data 2.3 | - | - | 2 weekly | next (aspatial) |
| layer 50794 | NZ Survey Plans | `survey_plans` | 1,208,452 | CC BY 4.0 | yes | - | 2 weekly | next (with its geometry) |
| table 51565 | NZ Parcel Statutory Actions List | `parcel_statutory_actions_list` | 343,849 | CC BY 4.0 | - | - | 2 weekly | next (aspatial) |
| table 114077 | NZ Properties: Parent Property | `properties_parent_property` | 338,363 | CC BY 4.0 | - | weekly | 2 weekly | next (aspatial) |
| table 114085 | NZ Properties: National District Valuation Roll | `properties_national_district_valuation_roll` | 288,061 | CC BY 4.0 | - | weekly | 2 weekly | next (aspatial) |
| layer 123109 | NZ Addresses: Road Sections | `addresses_road_sections` | 251,061 | CC BY 4.0 | yes | - | 2 weekly | next (with its geometry) |
| table 101291 | NZ Building Outlines Lifecycle (Deprecated) | `building_outlines_lifecycle_deprecated` | 206,197 | CC BY 4.0 | - | - | 2 weekly | next (aspatial) |
| table 118829 | NZ Untitled Land-Primary Parcel Association List (pilot) | `untitled_land_primary_parcel_association_list_pi` | 130,686 | CC BY 4.0 | - | weekly | 2 weekly | next (aspatial) |
| layer 120944 | NZ Property Untitled Land (pilot) | `property_untitled_land_pilot` | 89,260 | CC BY 4.0 | yes | weekly | 2 weekly | next (with its geometry) |
| layer 123110 | NZ Addresses: Roads | `addresses_roads` | 82,445 | CC BY 4.0 | yes | - | 2 weekly | next (with its geometry) |
| table 53561 | Protected Areas to Parcel Association | `protected_areas_to_parcel_association` | 55,038 | CC BY 4.0 | - | - | 2 weekly | next (aspatial) |
| table 110594 | Suburb Locality - Adjacent Name | `suburb_locality_adjacent_name` | 29,393 | CC BY 4.0 | - | - | 2 weekly | next (aspatial) |
| table 113761 | Suburb Locality - Population | `suburb_locality_population` | 29,393 | CC BY 4.0 | - | - | 2 weekly | next (aspatial) |
| table 118830 | NZ Properties: Property-Untitled Land Reference (pilot) | `properties_property_untitled_land_reference_pilo` | 25,003 | CC BY 4.0 | - | weekly | 2 weekly | next (aspatial) |
| layer 53564 | Protected Areas | `protected_areas` | 18,047 | CC BY 4.0 | yes | - | 2 weekly | next (with its geometry) |
| layer 52423 | NZ Place Names - Lines (NZGB) | `place_names_lines` | 18,027 | CC BY 4.0 | yes | - | 2 weekly | next (with its geometry) |
| table 53450 | LINZ Managed Crown Property to Parcel Association | `linz_managed_crown_property_to_parcel_associatio` | 14,902 | CC BY 4.0 | - | - | 2 weekly | next (aspatial) |
| layer 51570 | NZ Linear Parcels | `linear_parcels` | 12,411 | CC BY 4.0 | yes | - | 2 weekly | next (with its geometry) |
| layer 52424 | NZ Place Names - Polygons (NZGB) | `place_names_polygons` | 7,515 | CC BY 4.0 | yes | - | 2 weekly | next (with its geometry) |
| layer 113764 | NZ Suburbs and Localities | `suburbs_and_localities` | 6,563 | CC BY 4.0 | yes | - | 2 weekly | next (with its geometry) |
| layer 113763 | Suburb Locality | `suburb_locality` | 6,563 | CC BY 4.0 | yes | - | 2 weekly | next (with its geometry) |
| layer 53358 | LINZ Managed Crown Property | `linz_managed_crown_property` | 6,558 | CC BY 4.0 | yes | - | 2 weekly | next (with its geometry) |
| table 113008 | Suburb Locality - NZ Gazetteer | `suburb_locality_nz_gazetteer` | 6,346 | CC BY 4.0 | - | - | 2 weekly | next (aspatial) |
| table 110593 | Suburb Locality - Additional Name | `suburb_locality_additional_name` | 6,228 | CC BY 4.0 | - | - | 2 weekly | next (aspatial) |
| table 110596 | Suburb Locality - Territorial Authority | `suburb_locality_territorial_authority` | 5,915 | CC BY 4.0 | - | - | 2 weekly | next (aspatial) |
| table 113014 | Suburb Locality - Major Name | `suburb_locality_major_name` | 3,347 | CC BY 4.0 | - | - | 2 weekly | next (aspatial) |
| layer 105588 | NZ Facilities | `facilities` | 2,681 | CC BY 4.0 | yes | - | 2 weekly | next (with its geometry) |
| layer 117263 | Tangata Whenua Place Names | `tangata_whenua_place_names` | 1,748 | CC BY 4.0 | yes | - | 2 weekly | next (with its geometry) |
| table 124126 | NZ Properties: Sale Group | `properties_sale_group` | 919 | CC BY 4.0 | - | - | 2 weekly | next (aspatial) |
| table 105630 | NZ Properties: Property Category | `properties_property_category` | 548 | CC BY 4.0 | - | - | 2 weekly | next (aspatial) |
| table 105636 | NZ Properties: Zoning | `properties_zoning` | 238 | CC BY 4.0 | - | - | 2 weekly | next (aspatial) |
| layer 51572 | South Island Pastoral Leases | `south_island_pastoral_leases` | 180 | CC BY 4.0 | yes | - | 2 weekly | next (with its geometry) |
| table 105619 | NZ Properties: Building Construction | `properties_building_construction` | 169 | CC BY 4.0 | - | - | 2 weekly | next (aspatial) |
| layer 50840 | NZ Survey Capture Areas (SCA) | `survey_capture_areas` | 84 | CC BY 4.0 | yes | - | 2 weekly | next (with its geometry) |
| table 105616 | NZ Properties: Actual Property Use | `properties_actual_property_use` | 83 | CC BY 4.0 | - | - | 2 weekly | next (aspatial) |
| table 105618 | NZ Properties: Building Condition | `properties_building_condition` | 25 | CC BY 4.0 | - | - | 2 weekly | next (aspatial) |
| table 105617 | NZ Properties: Building Age | `properties_building_age` | 18 | CC BY 4.0 | - | - | 2 weekly | next (aspatial) |
| layer 50785 | NZ Land Districts | `land_districts` | 12 | CC BY 4.0 | yes | - | 2 weekly | next (with its geometry) |
| table 105620 | NZ Properties: Mass Contour | `properties_mass_contour` | 5 | CC BY 4.0 | - | - | 2 weekly | next (aspatial) |
| table 105627 | NZ Properties: Ownership | `properties_ownership` | 5 | CC BY 4.0 | - | - | 2 weekly | next (aspatial) |
| table 105623 | NZ Properties: Mass Scope of View | `properties_mass_scope_of_view` | 4 | CC BY 4.0 | - | - | 2 weekly | next (aspatial) |
| table 105633 | NZ Properties: Sale Tenure | `properties_sale_tenure` | 4 | CC BY 4.0 | - | - | 2 weekly | next (aspatial) |
| table 105634 | NZ Properties: Sale Type | `properties_sale_type` | 4 | CC BY 4.0 | - | - | 2 weekly | next (aspatial) |
| table 105624 | NZ Properties: Mass View | `properties_mass_view` | 3 | CC BY 4.0 | - | - | 2 weekly | next (aspatial) |
| table 105629 | NZ Properties: Price-Value Relationship | `properties_price_value_relationship` | 3 | CC BY 4.0 | - | - | 2 weekly | next (aspatial) |
| table 105621 | NZ Properties: Mass Decks | `properties_mass_decks` | 2 | CC BY 4.0 | - | - | 2 weekly | next (aspatial) |
| table 105622 | NZ Properties: Mass Other Improvements | `properties_mass_other_improvements` | 2 | CC BY 4.0 | - | - | 2 weekly | next (aspatial) |
| table 105625 | NZ Properties: Mass Workshop or Laundry | `properties_mass_workshop_or_laundry` | 2 | CC BY 4.0 | - | - | 2 weekly | next (aspatial) |
| table 105632 | NZ Properties: Rental Type | `properties_rental_type` | 2 | CC BY 4.0 | - | - | 2 weekly | next (aspatial) |
| table 52007 | Landonline: Title Memorial Text | `lol_title_memorial_text` | 49,543,730 | Personal Data 2.3 | - | - | 3 monthly | next (aspatial) |
| table 52006 | Landonline: Title Memorial | `lol_title_memorial` | 46,036,089 | CC BY 4.0 | - | - | 3 monthly | next (aspatial) |
| table 52002 | Landonline: Title Action | `lol_title_action` | 33,771,201 | CC BY 4.0 | - | - | 3 monthly | next (aspatial) |
| table 52013 | Landonline: Title Instrument Title | `lol_title_instrument_title` | 28,646,607 | CC BY 4.0 | - | - | 3 monthly | next (aspatial) |
| table 51994 | Landonline: Nominal Index | `lol_nominal_index` | 26,025,676 | Personal Data 2.3 | - | - | 3 monthly | next (aspatial) |
| table 51702 | Landonline: Action | `lol_action` | 22,721,764 | CC BY 4.0 | - | - | 3 monthly | next (aspatial) |
| table 52012 | Landonline: Title Instrument | `lol_title_instrument` | 18,814,086 | CC BY 4.0 | - | - | 3 monthly | next (aspatial) |
| table 51998 | Landonline: Proprietor | `lol_proprietor` | 16,944,633 | Personal Data 2.3 | - | - | 3 monthly | next (aspatial) |
| table 52065 | Landonline: Estate Share | `lol_estate_share` | 11,286,449 | Personal Data 2.3 | - | - | 3 monthly | next (aspatial) |
| table 51717 | Landonline: Legal Description Parcel | `lol_legal_description_parcel` | 7,602,175 | CC BY 4.0 | - | - | 3 monthly | next (aspatial) |
| layer 101292 | NZ Building Outlines (All Sources) | `building_outlines_all_sources` | 6,634,223 | CC BY 4.0 | yes | - | 3 monthly | next (with its geometry) |
| table 51986 | Landonline: Legal Description | `lol_legal_description` | 5,836,356 | CC BY 4.0 | - | - | 3 monthly | next (aspatial) |
| table 51590 | Landonline: Appellation | `lol_appellation` | 5,717,419 | CC BY 4.0 | - | - | 3 monthly | next (aspatial) |
| layer 51976 | Landonline: Parcel | `lol_parcel` | 5,500,688 | CC BY 4.0 | yes | - | 3 monthly | next (with its geometry) |
| table 51707 | Landonline: Affected Parcel | `lol_affected_parcel` | 5,345,220 | CC BY 4.0 | - | - | 3 monthly | next (aspatial) |
| layer 51996 | Landonline: Parcel Label | `lol_parcel_label` | 4,406,375 | CC BY 4.0 | yes | - | 3 monthly | next (with its geometry) |
| table 51997 | Landonline: Parcel Ring | `lol_parcel_ring` | 4,392,209 | CC BY 4.0 | - | - | 3 monthly | next (aspatial) |
| table 52067 | Landonline: Title | `lol_title` | 4,282,164 | CC BY 4.0 | - | - | 3 monthly | next (aspatial) |
| table 52010 | Landonline: Title Encumbrance | `lol_title_encumbrance` | 3,470,138 | CC BY 4.0 | - | - | 3 monthly | next (aspatial) |
| table 52068 | Landonline: Title Estate | `lol_title_estate` | 3,442,800 | CC BY 4.0 | - | - | 3 monthly | next (aspatial) |
| table 52011 | Landonline: Title Hierarchy | `lol_title_hierarchy` | 3,440,600 | CC BY 4.0 | - | - | 3 monthly | next (aspatial) |
| layer 50804 | NZ Property Titles (the title's shape: layer 50804 with its geometry) | `title_shapes` | 2,457,581 | CC BY 4.0 | yes | - | 3 monthly | next (with its geometry) |
| table 52069 | Landonline: Survey Plan Image Revision | `lol_survey_plan_image_revision` | 2,150,602 | CC BY 4.0 | - | - | 3 monthly | next (aspatial) |
| table 51984 | Landonline: Encumbrance | `lol_encumbrance` | 1,849,240 | CC BY 4.0 | - | - | 3 monthly | next (aspatial) |
| table 51985 | Landonline: Encumbrancee | `lol_encumbrancee` | 1,616,107 | Personal Data 2.3 | - | - | 3 monthly | next (aspatial) |
| layer 51747 | Landonline: Survey Plan Reference | `lol_survey_plan_reference` | 1,583,361 | CC BY 4.0 | yes | - | 3 monthly | next (with its geometry) |
| table 51983 | Landonline: Encumbrance Share | `lol_encumbrance_share` | 1,582,297 | CC BY 4.0 | - | - | 3 monthly | next (aspatial) |
| table 52014 | Landonline: Work | `lol_work` | 1,328,119 | CC BY 4.0 | - | - | 3 monthly | next (aspatial) |
| table 52001 | Landonline: Survey | `lol_survey` | 1,323,306 | CC BY 4.0 | - | - | 3 monthly | next (aspatial) |
| table 51708 | Landonline: Comprised In | `lol_comprised_in` | 466,297 | CC BY 4.0 | - | - | 3 monthly | next (aspatial) |
| table 51700 | Landonline: Statutory Action Parcel | `lol_statutory_action_parcel` | 343,849 | CC BY 4.0 | - | - | 3 monthly | next (aspatial) |
| table 51746 | Landonline: Survey Admin Area | `lol_survey_admin_area` | 293,794 | CC BY 4.0 | - | - | 3 monthly | next (aspatial) |
| table 51698 | Landonline: Statute Action | `lol_statute_action` | 188,218 | CC BY 4.0 | - | - | 3 monthly | next (aspatial) |
| table 52004 | Landonline: Title Document Reference | `lol_title_document_reference` | 168,822 | CC BY 4.0 | - | - | 3 monthly | next (aspatial) |
| table 51982 | Landonline: Alias | `lol_alias` | 168,168 | Personal Data 2.3 | - | - | 3 monthly | next (aspatial) |
| table 51743 | Landonline: Site | `lol_site` | 134,199 | CC BY 4.0 | - | - | 3 monthly | next (aspatial) |
| table 51744 | Landonline: Site Locality | `lol_site_locality` | 133,838 | CC BY 4.0 | - | - | 3 monthly | next (aspatial) |
| layer 52017 | Landonline: Feature Name Point | `lol_feature_name_point` | 58,081 | CC BY 4.0 | yes | - | 3 monthly | next (with its geometry) |
| layer 52016 | Landonline: Feature Name Polygon | `lol_feature_name_polygon` | 17,869 | CC BY 4.0 | yes | - | 3 monthly | next (with its geometry) |
| table 51648 | Landonline: System Code | `lol_system_code` | 14,612 | CC BY 4.0 | - | - | 3 monthly | next (aspatial) |
| layer 51977 | Landonline: Parcel Linestring | `lol_parcel_linestring` | 12,411 | CC BY 4.0 | yes | - | 3 monthly | next (with its geometry) |
| table 52062 | Landonline: User | `lol_user` | 4,317 | Personal Data 2.3 | - | - | 3 monthly | next (aspatial) |
| table 51699 | Landonline: Statute | `lol_statute` | 2,054 | CC BY 4.0 | - | - | 3 monthly | next (aspatial) |
| table 52000 | Landonline: Statistical Area | `lol_statistical_area` | 631 | CC BY 4.0 | - | - | 3 monthly | next (aspatial) |
| table 51593 | Landonline: System Code Group | `lol_system_code_group` | 553 | CC BY 4.0 | - | - | 3 monthly | next (aspatial) |
| table 52009 | Landonline: Transaction Type | `lol_transaction_type` | 527 | CC BY 4.0 | - | - | 3 monthly | next (aspatial) |
| layer 51718 | Landonline: Locality | `lol_locality` | 17 | CC BY 4.0 | yes | - | 3 monthly | next (with its geometry) |
| table 51728 | Landonline: Action Type | `lol_action_type` | 13 | CC BY 4.0 | - | - | 3 monthly | next (aspatial) |
| table 51999 | Landonline: Statistical Version | `lol_statistical_version` | 13 | CC BY 4.0 | - | - | 3 monthly | next (aspatial) |
| layer 52070 | Landonline: Land District | `lol_land_district` | 12 | CC BY 4.0 | yes | - | 3 monthly | next (with its geometry) |
| table 52066 | Landonline: Office | `lol_office` | 11 | CC BY 4.0 | - | - | 3 monthly | next (aspatial) |
| table 51742 | Landonline: Setup | `lol_setup` | 75,741,250 | CC BY 4.0 | - | - | 4 quarterly | next (aspatial) |
| table 51725 | Landonline: Observation | `lol_observation` | 74,958,167 | CC BY 4.0 | - | - | 4 quarterly | next (aspatial) |
| table 51724 | Landonline: Observation Accuracy | `lol_observation_accuracy` | 74,958,157 | CC BY 4.0 | - | - | 4 quarterly | next (aspatial) |
| layer 51694 | NZ Survey Observations (Cadastral) | `survey_observations` | 59,757,451 | CC BY 4.0 | yes | - | 4 quarterly | next (with its geometry) |
| table 51995 | Landonline: Parcel Dimension | `lol_parcel_dimension` | 52,667,123 | CC BY 4.0 | - | - | 4 quarterly | next (aspatial) |
| table 51723 | Landonline: Parcel Boundary | `lol_parcel_boundary` | 47,718,836 | CC BY 4.0 | - | - | 4 quarterly | next (aspatial) |
| table 89377 | Landonline: Ordinate Adjustment | `lol_ordinate_adjustment` | 41,520,758 | CC BY 4.0 | - | - | 4 quarterly | next (aspatial) |
| layer 51979 | Landonline: Vector | `lol_vector` | 30,603,483 | CC BY 4.0 | yes | - | 4 quarterly | next (with its geometry) |
| table 51729 | Landonline: Node Works | `lol_node_works` | 23,252,853 | CC BY 4.0 | - | - | 4 quarterly | next (aspatial) |
| layer 51975 | Landonline: Line | `lol_line` | 19,734,004 | CC BY 4.0 | yes | - | 4 quarterly | next (with its geometry) |
| table 51706 | Landonline: Adoption | `lol_adoption` | 18,849,426 | CC BY 4.0 | - | - | 4 quarterly | next (aspatial) |
| table 51990 | Landonline: Mark Physical State | `lol_mark_physical_state` | 18,717,209 | CC BY 4.0 | - | - | 4 quarterly | next (aspatial) |
| table 51989 | Landonline: Mark | `lol_mark` | 18,306,324 | CC BY 4.0 | - | - | 4 quarterly | next (aspatial) |
| table 52018 | Landonline: Coordinate | `lol_coordinate` | 18,260,800 | CC BY 4.0 | - | - | 4 quarterly | next (aspatial) |
| layer 51993 | Landonline: Node | `lol_node` | 18,234,417 | CC BY 4.0 | yes | - | 4 quarterly | next (with its geometry) |
| layer 50774 | NZ Survey Boundary Marks | `survey_boundary_marks` | 14,963,237 | CC BY 4.0 | yes | - | 4 quarterly | next (with its geometry) |
| table 51991 | Landonline: Mark Name | `lol_mark_name` | 12,449,795 | CC BY 4.0 | - | - | 4 quarterly | next (aspatial) |
| layer 50820 | NZ Survey Boundary Vectors | `survey_boundary_vectors` | 10,502,769 | CC BY 4.0 | yes | - | 4 quarterly | next (with its geometry) |
| layer 50776 | NZ Survey Non-Boundary Marks | `survey_non_boundary_marks` | 3,113,214 | CC BY 4.0 | yes | - | 4 quarterly | next (with its geometry) |
| table 51738 | Landonline: Reference Survey | `lol_reference_survey` | 1,735,264 | CC BY 4.0 | - | - | 4 quarterly | next (aspatial) |
| layer 50777 | NZ Cadastral Survey Network Marks | `cadastral_survey_network_marks` | 1,270,002 | CC BY 4.0 | yes | - | 4 quarterly | next (with its geometry) |
| table 51981 | Landonline: Adjustment Run | `lol_adjustment_run` | 519,155 | CC BY 4.0 | - | - | 4 quarterly | next (aspatial) |
| layer 52350 | NZ Christchurch Post-EQ Survey-Accurate (SDC) Boundary Coordinates | `christchurch_post_eq_survey_accurate_boundary_co` | 415,489 | CC BY 4.0 | yes | - | 4 quarterly | next (with its geometry) |
| layer 50778 | NZ Survey Arc Chords | `survey_arc_chords` | 385,876 | CC BY 4.0 | yes | - | 4 quarterly | next (with its geometry) |
| layer 50790 | NZ Cadastral Adjustments | `cadastral_adjustments` | 325,060 | CC BY 4.0 | yes | - | 4 quarterly | next (with its geometry) |
| table 51988 | Landonline: Maintenance | `lol_maintenance` | 96,534 | CC BY 4.0 | - | - | 4 quarterly | next (aspatial) |
| table 51727 | Landonline: Mark Supporting Document | `lol_mark_supporting_document` | 72,025 | CC BY 4.0 | - | - | 4 quarterly | next (aspatial) |
| layer 51980 | Landonline: Vector Point | `lol_vector_point` | 71,096 | CC BY 4.0 | yes | - | 4 quarterly | next (with its geometry) |
| table 51992 | Landonline: Node Proposed Order | `lol_node_proposed_order` | 66,089 | CC BY 4.0 | - | - | 4 quarterly | next (aspatial) |
| table 51703 | Landonline: Adjustment User Coefficient | `lol_adjustment_user_coefficient` | 56,829 | CC BY 4.0 | - | - | 4 quarterly | next (aspatial) |
| layer 52349 | NZ Christchurch Post-EQ Survey-Accurate (SDC) Non-Boundary Coordinates | `christchurch_post_eq_survey_accurate_non_boundar` | 50,181 | CC BY 4.0 | yes | - | 4 quarterly | next (with its geometry) |
| layer 53455 | Canterbury Earthquake Survey Mark Movements | `canterbury_earthquake_survey_mark_movements` | 8,882 | CC BY 4.0 | yes | - | 4 quarterly | next (with its geometry) |
| layer 50836 | NZ WACA Adjustments | `waca_adjustments` | 4,462 | CC BY 4.0 | yes | - | 4 quarterly | next (with its geometry) |
| table 51737 | Landonline: Reduction Run | `lol_reduction_run` | 4,265 | CC BY 4.0 | - | - | 4 quarterly | next (aspatial) |
| table 51704 | Landonline: Adjustment Coefficient | `lol_adjustment_coefficient` | 3,552 | CC BY 4.0 | - | - | 4 quarterly | next (aspatial) |
| layer 51588 | Canterbury Earthquake Geodetic Marks (2010, 2011) - Comprehensive | `canterbury_earthquake_geodetic_marks_comprehensi` | 818 | CC BY 4.0 | yes | - | 4 quarterly | next (with its geometry) |
| layer 51589 | Canterbury Earthquake Geodetic Marks (2010, 2011) - Simple | `canterbury_earthquake_geodetic_marks_simple` | 719 | CC BY 4.0 | yes | - | 4 quarterly | next (with its geometry) |
| layer 51688 | Canterbury Earthquake Precise-Levelling Heights (2010, 2011) | `canterbury_earthquake_precise_levelling_heights` | 600 | CC BY 4.0 | yes | - | 4 quarterly | next (with its geometry) |
| table 51711 | Landonline: Coordinate Precision | `lol_coordinate_precision` | 550 | CC BY 4.0 | - | - | 4 quarterly | next (aspatial) |
| table 51731 | Landonline: Observation Set | `lol_observation_set` | 456 | CC BY 4.0 | - | - | 4 quarterly | next (aspatial) |
| table 51709 | Landonline: Coordinate System | `lol_coordinate_system` | 435 | CC BY 4.0 | - | - | 4 quarterly | next (aspatial) |
| layer 50835 | NZ SPI Adjustments | `spi_adjustments` | 396 | CC BY 4.0 | yes | - | 4 quarterly | next (with its geometry) |
| table 51713 | Landonline: Datum | `lol_datum` | 365 | CC BY 4.0 | - | - | 4 quarterly | next (aspatial) |
| table 51712 | Landonline: Coordinate Order | `lol_coordinate_order` | 240 | CC BY 4.0 | - | - | 4 quarterly | next (aspatial) |
| layer 53527 | NZ Kaikoura Earthquake (14 Nov 2016) Geodetic Marks | `kaikoura_earthquake_geodetic_marks` | 158 | CC BY 4.0 | yes | - | 4 quarterly | next (with its geometry) |
| layer 53322 | Canterbury Earthquake (14 Feb 2016) Geodetic Marks | `canterbury_earthquake_geodetic_marks` | 149 | CC BY 4.0 | yes | - | 4 quarterly | next (with its geometry) |
| table 51705 | Landonline: Adjustment Method | `lol_adjustment_method` | 90 | CC BY 4.0 | - | - | 4 quarterly | next (aspatial) |
| table 51710 | Landonline: Coordinate Type | `lol_coordinate_type` | 74 | CC BY 4.0 | - | - | 4 quarterly | next (aspatial) |
| table 51730 | Landonline: Observation Element Type | `lol_observation_element_type` | 25 | CC BY 4.0 | - | - | 4 quarterly | next (aspatial) |
| table 51732 | Landonline: Observation Type | `lol_observation_type` | 21 | CC BY 4.0 | - | - | 4 quarterly | next (aspatial) |
| table 51748 | Landonline: Unit Of Measure | `lol_unit_of_measure` | 21 | CC BY 4.0 | - | - | 4 quarterly | next (aspatial) |
| table 51736 | Landonline: Reduction Method | `lol_reduction_method` | 11 | CC BY 4.0 | - | - | 4 quarterly | next (aspatial) |
| table 51735 | Landonline: Ordinate Type | `lol_ordinate_type` | 9 | CC BY 4.0 | - | - | 4 quarterly | next (aspatial) |
| table 51715 | Landonline: Ellipsoid | `lol_ellipsoid` | 4 | CC BY 4.0 | - | - | 4 quarterly | next (aspatial) |
| layer 51733 | Landonline: Official Coordinate System | `lol_official_coordinate_system` | 3 | CC BY 4.0 | yes | - | 4 quarterly | next (with its geometry) |
| layer 106965 | NZ 1:500 Tile Index | `1_500_tile_index` | 5,090,000 | CC BY 4.0 | yes | - | - | not taken: a map-sheet tile index, not land |
| layer 50806 | NZ Property Title Owners | `property_title_owners` | 5,014,362 | Personal Data 2.3 | yes | - | - | not taken: the owners of table 51564 with the shapes of their titles' parcels, both held |
| layer 53418 | NZ Quasigeoid 2016 | `quasigeoid_2016` | 3,783,901 | CC BY 4.0 | yes | - | - | not taken: a geodetic grid (a datum or height transform), not land held or bounded |
| table 52008 | Landonline: Title Parcel Association | `lol_title_parcel_association` | 3,000,734 | CC BY 4.0 | - | - | - | not taken: the same rows as table 51569 (the association list), held whole |
| layer 50772 | NZ Primary Parcels | `primary_parcels` | 2,802,079 | CC BY 4.0 | yes | - | - | not taken: a subset of the rows of layer 51571, held whole |
| layer 50823 | NZ Primary Land Parcels | `primary_land_parcels` | 2,467,194 | CC BY 4.0 | yes | - | - | not taken: a subset of the rows of layer 51571, held whole |
| layer 50805 | NZ Property Titles Including Owners | `property_titles_including_owners` | 2,457,581 | Personal Data 2.3 | yes | - | - | not taken: the rows of layer 50804 with the owners of table 51564 joined in, both held |
| layer 104692 | NZ 1:1k Tile Index | `1_1k_tile_index` | 1,272,500 | CC BY 4.0 | yes | - | - | not taken: a map-sheet tile index, not land |
| layer 50782 | NZ Non-Primary Parcels | `non_primary_parcels` | 888,759 | CC BY 4.0 | yes | - | - | not taken: a subset of the rows of layer 51571, held whole |
| layer 51002 | NZ Aerial Photo Footprints, Mainland NZ, (1936-2008) polygons | `aerial_photo_footprints_mainland_nz_polygons` | 706,828 | CC BY 4.0 | yes | - | - | not taken: an index of imagery or elevation surveys, not land |
| layer 106966 | NZ 1:2k Tile Index | `1_2k_tile_index` | 318,125 | CC BY 4.0 | yes | - | - | not taken: a map-sheet tile index, not land |
| layer 50796 | NZ Primary Road Parcels | `primary_road_parcels` | 309,400 | CC BY 4.0 | yes | - | - | not taken: a subset of the rows of layer 51571, held whole |
| layer 53431 | Lyttelton 1937 to NZGD2000 Conversion | `lyttelton_1937_to_nzgd2000_conversion` | 78,547 | CC BY 4.0 | yes | - | - | not taken: a geodetic grid (a datum or height transform), not land held or bounded |
| layer 53433 | Moturiki 1953 to NZGD2000 Conversion | `moturiki_1953_to_nzgd2000_conversion` | 57,937 | CC BY 4.0 | yes | - | - | not taken: a geodetic grid (a datum or height transform), not land held or bounded |
| layer 104691 | NZ 1:5k Tile Index | `1_5k_tile_index` | 50,900 | CC BY 4.0 | yes | - | - | not taken: a map-sheet tile index, not land |
| layer 53443 | Taranaki 1970 to NZGD2000 Conversion | `taranaki_1970_to_nzgd2000_conversion` | 28,561 | CC BY 4.0 | yes | - | - | not taken: a geodetic grid (a datum or height transform), not land held or bounded |
| layer 53427 | Dunedin 1958 to NZGD2000 Conversion | `dunedin_1958_to_nzgd2000_conversion` | 27,475 | CC BY 4.0 | yes | - | - | not taken: a geodetic grid (a datum or height transform), not land held or bounded |
| layer 53437 | Nelson 1955 to NZGD2000 Conversion | `nelson_1955_to_nzgd2000_conversion` | 25,993 | CC BY 4.0 | yes | - | - | not taken: a geodetic grid (a datum or height transform), not land held or bounded |
| layer 50771 | NZ Primary Hydro Parcels | `primary_hydro_parcels` | 25,485 | CC BY 4.0 | yes | - | - | not taken: a subset of the rows of layer 51571, held whole |
| layer 53439 | One Tree Point 1964 to NZGD2000 Conversion | `one_tree_point_1964_to_nzgd2000_conversion` | 21,895 | CC BY 4.0 | yes | - | - | not taken: a geodetic grid (a datum or height transform), not land held or bounded |
| layer 53432 | Lyttelton 1937 to NZVD2016 Conversion | `lyttelton_1937_to_nzvd2016_conversion` | 19,665 | CC BY 4.0 | yes | - | - | not taken: a geodetic grid (a datum or height transform), not land held or bounded |
| layer 53445 | Wellington 1953 to NZGD2000 Conversion | `wellington_1953_to_nzgd2000_conversion` | 18,271 | CC BY 4.0 | yes | - | - | not taken: a geodetic grid (a datum or height transform), not land held or bounded |
| layer 53435 | Napier 1962 to NZGD2000 Conversion | `napier_1962_to_nzgd2000_conversion` | 16,819 | CC BY 4.0 | yes | - | - | not taken: a geodetic grid (a datum or height transform), not land held or bounded |
| layer 53425 | Dunedin-Bluff 1960 to NZGD2000 Conversion | `dunedin_bluff_1960_to_nzgd2000_conversion` | 15,553 | CC BY 4.0 | yes | - | - | not taken: a geodetic grid (a datum or height transform), not land held or bounded |
| layer 53416 | Auckland 1946 to NZGD2000 Conversion | `auckland_1946_to_nzgd2000_conversion` | 15,295 | CC BY 4.0 | yes | - | - | not taken: a geodetic grid (a datum or height transform), not land held or bounded |
| layer 53448 | Moturiki 1953 to NZVD2016 Conversion | `moturiki_1953_to_nzvd2016_conversion` | 14,364 | CC BY 4.0 | yes | - | - | not taken: a geodetic grid (a datum or height transform), not land held or bounded |
| layer 104690 | NZ 1:10k Tile Index | `1_10k_tile_index` | 12,725 | CC BY 4.0 | yes | - | - | not taken: a map-sheet tile index, not land |
| layer 53429 | Gisborne 1926 to NZGD2000 Conversion | `gisborne_1926_to_nzgd2000_conversion` | 9,409 | CC BY 4.0 | yes | - | - | not taken: a geodetic grid (a datum or height transform), not land held or bounded |
| layer 50783 | NZ Non-Primary Linear Parcels | `non_primary_linear_parcels` | 9,185 | CC BY 4.0 | yes | - | - | not taken: a subset of the rows of layer 51570, held whole |
| layer 53444 | Taranaki 1970 to NZVD2016 Conversion | `taranaki_1970_to_nzvd2016_conversion` | 7,225 | CC BY 4.0 | yes | - | - | not taken: a geodetic grid (a datum or height transform), not land held or bounded |
| layer 53428 | Dunedin 1958 to NZVD2016 Conversion | `dunedin_1958_to_nzvd2016_conversion` | 6,952 | CC BY 4.0 | yes | - | - | not taken: a geodetic grid (a datum or height transform), not land held or bounded |
| layer 53438 | Nelson 1955 to NZVD2016 Conversion | `nelson_1955_to_nzvd2016_conversion` | 6,580 | CC BY 4.0 | yes | - | - | not taken: a geodetic grid (a datum or height transform), not land held or bounded |
| layer 53441 | Stewart Island 1977 to NZGD2000 Conversion | `stewart_island_1977_to_nzgd2000_conversion` | 5,917 | CC BY 4.0 | yes | - | - | not taken: a geodetic grid (a datum or height transform), not land held or bounded |
| layer 53440 | One Tree Point 1964 to NZVD2016 Conversion | `one_tree_point_1964_to_nzvd2016_conversion` | 5,548 | CC BY 4.0 | yes | - | - | not taken: a geodetic grid (a datum or height transform), not land held or bounded |
| layer 53446 | Wellington 1953 to NZVD2016 Conversion | `wellington_1953_to_nzvd2016_conversion` | 4,636 | CC BY 4.0 | yes | - | - | not taken: a geodetic grid (a datum or height transform), not land held or bounded |
| layer 53436 | Napier 1962 to NZVD2016 Conversion | `napier_1962_to_nzvd2016_conversion` | 4,270 | CC BY 4.0 | yes | - | - | not taken: a geodetic grid (a datum or height transform), not land held or bounded |
| layer 53426 | Dunedin-Bluff 1960 to NZVD2016 Conversion | `dunedin_bluff_1960_to_nzvd2016_conversion` | 3,952 | CC BY 4.0 | yes | - | - | not taken: a geodetic grid (a datum or height transform), not land held or bounded |
| layer 53417 | Auckland 1946 to NZVD2016 Conversion | `auckland_1946_to_nzvd2016_conversion` | 3,886 | CC BY 4.0 | yes | - | - | not taken: a geodetic grid (a datum or height transform), not land held or bounded |
| layer 53430 | Gisborne 1926 to NZVD2016 Conversion | `gisborne_1926_to_nzvd2016_conversion` | 2,401 | CC BY 4.0 | yes | - | - | not taken: a geodetic grid (a datum or height transform), not land held or bounded |
| layer 53442 | Stewart Island 1977 to NZVD2016 Conversion | `stewart_island_1977_to_nzvd2016_conversion` | 1,519 | CC BY 4.0 | yes | - | - | not taken: a geodetic grid (a datum or height transform), not land held or bounded |
| layer 53423 | Bluff 1955 to NZGD2000 Conversion | `bluff_1955_to_nzgd2000_conversion` | 1,333 | CC BY 4.0 | yes | - | - | not taken: a geodetic grid (a datum or height transform), not land held or bounded |
| layer 95677 | NZ Imagery Survey Index | `imagery_survey_index` | 758 | CC BY 4.0 | yes | - | - | not taken: an index of imagery or elevation surveys, not land |
| layer 50780 | NZ Strata Parcels | `strata_parcels` | 742 | CC BY 4.0 | yes | - | - | not taken: a subset of the rows of layer 51571, held whole |
| layer 104687 | NZ 1:50k Tile Index | `1_50k_tile_index` | 509 | CC BY 4.0 | yes | - | - | not taken: a map-sheet tile index, not land |
| layer 123697 | Tide Stations | `tide_stations` | 428 | CC BY 4.0 | yes | - | - | not taken: a marine record, not land |
| layer 53424 | Bluff 1955 to NZVD2016 Conversion | `bluff_1955_to_nzvd2016_conversion` | 352 | CC BY 4.0 | yes | - | - | not taken: a geodetic grid (a datum or height transform), not land held or bounded |
| layer 104252 | NZ Elevation Survey Index | `elevation_survey_index` | 107 | CC BY 4.0 | yes | - | - | not taken: an index of imagery or elevation surveys, not land |
| layer 50781 | NZ Railway Centre Lines | `railway_centre_lines` | 59 | CC BY 4.0 | yes | - | - | not taken: a topographic line feature, no title, parcel or holding |
| layer 53419 | NZ Height Conversion Index | `height_conversion_index` | 13 | CC BY 4.0 | yes | - | - | not taken: a geodetic grid (a datum or height transform), not land held or bounded |
| layer 51684 | NZGD2000 deformation model version 2013-08-01 reverse patch coordinate shifts contours | `nzgd2000_deformation_model_version_2013_08_01_re` | 7 | CC BY 4.0 | yes | - | - | not taken: a geodetic grid (a datum or height transform), not land held or bounded |
| layer 51685 | NZGD2000 deformation model version 2013-08-01 reverse patch coordinate shifts filled contours | `nzgd2000_deformation_model_version_2013_51685` | 7 | CC BY 4.0 | yes | - | - | not taken: a geodetic grid (a datum or height transform), not land held or bounded |

## Not taken, and what is asked

- The 1,634 topographic, hydrographic and imagery entries outside the 222: maps, not land held or bounded.
- Of the 222, 51 are not taken: 30 geodetic grids (datum and height conversions, the quasigeoid, the deformation
  model), 6 map-sheet tile indexes, 3 imagery or elevation survey indexes, the tide stations, the railway centre lines;
  7 parcel layers that are filters of NZ Parcels (layer 51571, held whole: primary, non-primary, primary land, road,
  hydro, strata, non-primary linear) and the Landonline title-parcel association (the same rows as table 51569); and
  layers 50805 and 50806, which are the titles and the owners list joined, both held.
- No PostGIS: the database has no `postgis` extension available (`pg_available_extensions` lists `cube`,
  `earthdistance` and `btree_gist`, none installed). The geometry is held as GeoJSON text with its box, and the joins run
  in Python (`registers/linz/geo.py`). Installing PostGIS (the `postgis` package for PostgreSQL 18 and `CREATE EXTENSION
  postgis` in `querynz_v4`) would let a parcel and an address meet in SQL with a spatial index; asked of the integrator,
  not done.
- Disk: the document store has 2.9 TB free; the database's disk 690 GB. A billion rows as JSON may take some 300 GB in
  the database. The capture stops when the store has under 200 GB free; the load stages no catalogue source while the
  database's disk has under 150 GB free, and says so.
