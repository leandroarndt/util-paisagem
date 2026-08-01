# Útil paisagem changelog

## 0.3.0rc3

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
- Corrected images being pushed south on the northern hemisphere ([reported by Iomar and Zakharov at the FlightGear forum](https://forum.flightgear.org/viewtopic.php?f=5&t=44533))

## 0.2.0

- Connection settings (FlightGear telnet host, port, following interval).
- Tabbed settings window.
- Settings window shows error dialogs when trying to apply invalid integer entries.
- Telnet connection timeout reduced from 2 seconds to 1 second.
- Added "Found a bug?" menu item.
- "Latest release" menu item now opens latest production release only.

## 0.1.0

- Initial release.