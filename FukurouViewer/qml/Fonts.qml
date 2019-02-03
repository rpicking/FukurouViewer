pragma Singleton

import QtQuick 2.0

Item {
    id: fonts

    readonly property FontLoader fontAwesomeRegular: FontLoader {
        source: "./fonts/Font Awesome 5 Brands-Regular-400.otf"
    }
    readonly property FontLoader fontAwesomeSolid: FontLoader {
        source: "./fonts/Font Awesome 5 Free-Solid-900.otf"
    }
    readonly property FontLoader fontAwesomeBrands: FontLoader {
        source: "./fonts/Font Awesome 5 Brands-Regular-400.otf"
    }

    readonly property string icons: fonts.fontAwesomeRegular.name
    readonly property string solidIcons: fonts.fontAwesomeSolid.name
    readonly property string brands: fonts.fontAwesomeBrands.name    
}
