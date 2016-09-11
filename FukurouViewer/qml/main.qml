import QtQuick 2.5
import Qt.labs.settings 1.0
import QtQuick.Controls 1.4
import QtQuick.Controls.Styles 1.4
import QtQuick.Layouts 1.2

import "MyTheme.js" as Theme

ApplicationWindow {
    id: mainWindow
    color: Theme.backColor
    title: "Fukurou Viewer"

    Settings {
        property alias x: mainWindow.x
        property alias y: mainWindow.y
        property alias width: mainWindow.width
        property alias height: mainWindow.height
    }

    width: 1200
    height: 1100


    MouseArea {
        id: mainMouseArea
        anchors.rightMargin: 0
        anchors.bottomMargin: 0
        anchors.leftMargin: 0
        anchors.topMargin: 0
        anchors.fill: parent
        propagateComposedEvents: true
        onClicked: {
            forceActiveFocus()
        }

        Rectangle {
            id: topBar
            height: childrenRect.height * 2
            color: Theme.mainColor
            Layout.fillWidth: true
            border.width: 0
            anchors.right: parent.right
            anchors.rightMargin: 0
            anchors.left: parent.left
            anchors.leftMargin: 0
            anchors.top: parent.top
            anchors.topMargin: 0

            Label {
                id: name
                y: 28
                color: Theme.backColor
                text: "Fukurou Viewer"
                anchors.left: parent.left
                anchors.leftMargin: 6
                anchors.verticalCenter: searchRect.verticalCenter
                font.pointSize: 18
                font.family: mainFont.name
            }

            Rectangle {
                id: searchRect
                x: 16
                y: 16
                height: 36
                color: "#ffffff"
                radius: 5
                anchors.rightMargin: 6
                anchors.right: sortButton.left
                anchors.left: name.right
                anchors.leftMargin: 8
                anchors.top: parent.top
                anchors.topMargin: 16
                border.width: 1

                Label {
                    id: searchIcon
                    color: Theme.fontColorB
                    text: "\uf002"
                    anchors.verticalCenterOffset: 0
                    anchors.verticalCenter: parent.verticalCenter
                    anchors.leftMargin: 8
                    font.family: fontAwesome.name
                    font.pixelSize: 20
                    anchors.left: parent.left

                }

                TextField {
                    id: searchText
                    anchors.right: clearIcon.left
                    anchors.rightMargin: 0
                    font.family: "Verdana"
                    placeholderText: "Search"
                    font.pointSize: 12
                    anchors.bottomMargin: 1
                    anchors.topMargin: 1
                    anchors.left: searchIcon.right
                    anchors.bottom: parent.bottom
                    anchors.top: parent.top
                    anchors.leftMargin: 0
                    style: TextFieldStyle {
                        background: Rectangle {
                            border.width: 0

                        }
                    }
                }

                Button {
                    id: clearIcon
                    width: 24
                    height: 24
                    visible: searchText.text !== ""
                    action: Action {
                        onTriggered: {
                            searchText.text = ""
                        }
                    }

                    style: ButtonStyle {
                        label: Text {
                            font.family: fontAwesome.name
                            font.pixelSize: 20
                            text: "\uf00d"
                            color: Theme.fontColorB
                            verticalAlignment: Text.AlignVCenter
                        }
                        background: Rectangle {
                            color: "transparent"
                        }
                    }
                    anchors.verticalCenter: parent.verticalCenter
                    anchors.right: parent.right
                    anchors.rightMargin: 6
                }
            }
            Button {
                id: sortButton
                width: 34
                height: 34
                anchors.right: settingsButton.left
                anchors.rightMargin: 6
                anchors.verticalCenter: searchRect.verticalCenter
                onClicked: {
                    sortMenu.forceActiveFocus()
                }
                style: ButtonStyle {
                    label: Text {
                        font.family: materials.name
                        font.pixelSize: 32
                        text: "\uE164"
                        color: Theme.backColor
                        verticalAlignment: Text.AlignVCenter
                    }
                    background: Rectangle {
                        color: "transparent"
                    }
                }
            }

            Button {
                id: settingsButton
                width: 34
                height: 34
                anchors.right: parent.right
                anchors.rightMargin: 6
                anchors.verticalCenter: searchRect.verticalCenter
                style: ButtonStyle {
                    label: Text {
                        font.family: materials.name
                        font.pixelSize: 32
                        text: "\uE5D2"
                        color: Theme.backColor
                        verticalAlignment: Text.AlignVCenter
                    }
                    background: Rectangle {
                        color: "transparent"
                    }
                }
                MouseArea {
                    anchors.fill: parent
                    onClicked: {
                        settingsMenu.forceActiveFocus()
                    }
                }
            }
        }


        Button {
            id: button1
            x: 360
            y: 752
            text: qsTr("Button")
            onClicked: {
                sortDrop.forceActiveFocus()
            }
        }

        Rectangle {
            id: sortMenu
            x: 963
            width: sortField.width + 20
            height: sortField.height + 20
            color: "#ffffff"
            border.width: 0
            visible: activeFocus
            anchors.top: topBar.bottom
            anchors.topMargin: 10
            anchors.right: parent.right
            anchors.rightMargin: 10

            MouseArea {
                id: mouseArea1
                anchors.fill: parent
                onClicked: {
                    sortMenu.forceActiveFocus()
                }
            }

            ColumnLayout {
                id: sortField
                anchors.horizontalCenter: parent.horizontalCenter
                anchors.verticalCenter: parent.verticalCenter
                spacing: 40

                Label {
                    id: sortTitle
                    text: qsTr("Sort by")
                    font.pointSize: 12
                }

                RowLayout {
                    id: sortButtons
                    anchors.horizontalCenter: parent.horizontalCenter
                    anchors.verticalCenter: parent.verticalCenter
                    spacing: 10

                    ColumnLayout {
                        id: sortColumn
                        width: 100
                        height: 100
                        spacing: 5

                        ExclusiveGroup { id: sorting }
                        RadioButton {
                            id: nameSort
                            text: qsTr("NAME")
                            exclusiveGroup: sorting
                            style: RadioButtonStyle {
                                spacing: 10
                            }
                        }

                        RadioButton {
                            id: artistSort
                            text: qsTr("ARTIST")
                            exclusiveGroup: sorting
                            style: RadioButtonStyle {
                                spacing: 10
                            }
                        }

                        RadioButton {
                            id: countSort
                            text: qsTr("READ COUND")
                            exclusiveGroup: sorting
                            style: RadioButtonStyle {
                                spacing: 10
                            }
                        }

                        RadioButton {
                            id: dateSort
                            text: qsTr("DATE ADDED")
                            exclusiveGroup: sorting
                            style: RadioButtonStyle {
                                spacing: 10
                            }
                        }

                        RadioButton {
                            id: lastSort
                            text: qsTr("LAST READ")
                            exclusiveGroup: sorting
                            style: RadioButtonStyle {
                                spacing: 10
                            }
                        }

                        RadioButton {
                            id: ratingSort
                            text: qsTr("RATING")
                            exclusiveGroup: sorting
                            style: RadioButtonStyle {
                                spacing: 10
                            }
                        }

                        RadioButton {
                            id: tagSort
                            text: qsTr("TAG")
                            exclusiveGroup: sorting
                            style: RadioButtonStyle {
                                spacing: 10
                            }
                        }

                    }

                    ColumnLayout {
                        id: updownColumn
                        width: 100
                        height: 100
                        Layout.alignment: Qt.AlignLeft | Qt.AlignTop
                        spacing: 5

                        ExclusiveGroup { id: direction }

                        RadioButton {
                            id: ascendSort
                            text: qsTr("ASCENDING")
                            exclusiveGroup: direction
                            style: RadioButtonStyle {
                                spacing: 10
                            }
                        }

                        RadioButton {
                            id: descendSort
                            text: qsTr("DESCENDING")
                            exclusiveGroup: direction
                            style: RadioButtonStyle {
                                spacing: 10
                            }
                        }
                    }
                }

            }


        }

        Rectangle {
            id: settingMenu
            width: settingField.width
            height: settingField.height
            color: "#ffffff"
            anchors.right: parent.right
            anchors.rightMargin: 10
            anchors.top: topBar.bottom
            anchors.topMargin: 10

            MouseArea {
                id: mouseArea2
                anchors.fill: parent
            }

            ColumnLayout {
                id: settingField
                width: childrenRect.width
                height: 100
                spacing: 5

                Rectangle {
                    id: sbutton1
                    width: sbutton1lay.width + 20
                    height: sbutton1lay.height
                    color: "#ffffff"

                    RowLayout {
                        id: sbutton1lay
                        anchors.horizontalCenter: parent.horizontalCenter
                        anchors.verticalCenter: parent.verticalCenter
                        spacing: 20
                        Layout.fillWidth: true
                        Layout.alignment: Qt.AlignHCenter | Qt.AlignVCenter

                        Label {
                            id: label2
                            font.family: materials.name
                            text: "\uE8B8"
                            color: "#e6363434"
                            font.pointSize: 28
                        }

                        Label {
                            id: label3
                            text: qsTr("Settings")
                            color: "#e6363434"
                            font.pointSize: 18
                        }
                    }

                    MouseArea {
                        id: mouseArea3
                        hoverEnabled: true
                        anchors.fill: parent
                        onEntered: {
                            sbutton1.color = "#a6a6a6"
                        }
                        onExited: {
                            sbutton1.color = "#ffffff"
                        }
                    }
                }
            }
        }

        Rectangle {
            id: galleryToolTip
            x: 244
            y: 299
            width: childrenRect.width + 30
            height: childrenRect.height + 30
            color: "#e6363434"
            visible: true
            z: 1

            Label {
                id: label1
                x: 15
                y: 15
                color: Theme.backColor
                font.family: mainFont.name
                text: "Read 6 times\nLast read now\nArtist:\tcyocyo, cyocyopolice\nCharacter:\taguri madoka, ako shirabe\nFemale:\tbikini, bondage, galasses, mcnfjsxlaskjdf;\n\tlaskjf;alskj\nGroup:\tlonghorntrain\nLanguage:\tenglish, translated\nMale:\tdark skin\nNone:\tchocho, full color, group\nParody:\tdokidoki precure, suite precure"
                wrapMode: Text.NoWrap
                font.pointSize: 11
                textFormat: Text.AutoText
                verticalAlignment: Text.AlignTop
            }
        }





    }

    FontLoader {
        id: fontAwesome
        source: "fonts/fontawesome-webfont.ttf"
    }

    FontLoader {
        id: mainFont
        source: "fonts/Lato-Regular.ttf"
    }
    FontLoader {
        id: materials
        source: "fonts/googlematerials.ttf"
    }

}
