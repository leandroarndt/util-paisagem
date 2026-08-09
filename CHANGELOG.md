# Útil paisagem changelog

## 0.5.0rc1

- Renews tiles (new image download) after configurable amount of time.
- Provides tile visualizaton, including their state: good, downloaded after error management,
or needing renewal.
- Limits disk usage based on user preferences.

## 0.4.0

- Added image file format to the settings.
- Added threading to tile download and the corresponding setting
to the GUI.
- Empties waypoint name on deletion.
- Moved download resolution to the "download" tab in settings.
- Fixed issue #6 about Windows installations (with embedable Python)
not showing the tile image (it now opens the parent folder).
- Doesn't try to download latitudes greater than 85 degrees (ArcGIS
does not provide them — issue #5).

### 0.4.1

- Fixed an issue which could make download threads run for a long
time in background after closing the app in some situations.
- Application icon

### 0.4.2

- Fixed issue with wrong path being renamed at the settings window.
[Reported and corrected by Zakharov at the FlightGear
Forum.](https://forum.flightgear.org/viewtopic.php?f=5&t=44533&p=440908#p440904)

### 0.4.3

- Corrects tile width calculations on some parts of the southern
hemisphere.

## 0.3.0

- Windows installer
- Rename waypoints
- Added context menus on map:
  - Select tile.
  - Add waypoint.
- Left click on markers centers the map and selects their tiles.
- Added "file" menu:
  - Show orthophotos folder
  - Show tile image
  - Delete tile
- Added "edit" menu:
  - Copy coordinates
  - Copy tile index
  - Settings
- Search with "return" at the search bar and add waypoint on search with "ctrl+return"
- Created a workaround for the bug [reported by Patamoi on FlightGear forum](https://forum.flightgear.org/viewtopic.php?f=5&t=44533&p=440849#p440835)
which consisted of babel.numbers.format_decimal throwing babel.core.UnknownLocaleError on windows with locale "spanish_CHILE" (issue #3).
- Corrected images being pushed south on the northern hemisphere ([reported by lomar and Zakharov at the FlightGear forum](https://forum.flightgear.org/viewtopic.php?f=5&t=44533))

## 0.2.0

- Connection settings (FlightGear telnet host, port, following interval).
- Tabbed settings window.
- Settings window shows error dialogs when trying to apply invalid integer entries.
- Telnet connection timeout reduced from 2 seconds to 1 second.
- Added "Found a bug?" menu item.
- "Latest release" menu item now opens latest production release only.

## 0.1.0

- Initial release.