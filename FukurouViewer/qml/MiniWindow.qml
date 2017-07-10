import QtQuick 2.0
import QtQuick.Window 2.2
import QtQuick.Dialogs 1.2
import QtQuick.Layouts 1.1
import QtQuick.Controls 2.1
import QtQuick.Controls 1.4
import QtQuick.Controls.Styles 1.4

import "controls" as Awesome

Window {
    id: window
    //visible: false
    flags: Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint
    width: 400
    height: 640

    Component.onCompleted: {
        mainWindow.receiveHistory.connect(setHistory);
        mainWindow.receiveFolders.connect(setFolders);
        mainWindow.onWindowClose.connect(closeWindow);
    }

    onActiveChanged: {
        if(!active && (folderPopup.visible === false)) {
            closeWindow();
        }
    }

    function openWindow(_x, _y) {
        x = _x - width;
        y = _y - height;
        show();
        requestActivate();
        mainWindow.requestHistory(0);   //0 = get all history
        mainWindow.requestFolders();
        //console.log(active);
    }

    function closeWindow() {
        topBar.forceActiveFocus();
        hide();
    }

    function setHistory(items) {
        historyModel.clear();

        var monthNames = [
            "January", "February", "March",
            "April", "May", "June", "July",
            "August", "September", "October",
            "November", "December"
        ];

        for(var i = 0; i < items.length; ++i) {
            var d = new Date(items[i].time_added * 1000);
            var month = monthNames[d.getMonth()];
            var day = d.getDate();
            var year = d.getFullYear();
            items[i]["date"] = month + ' ' + day + ', ' + year
            historyModel.append(items[i]);
        }
    }

    function setFolders(items) {
        foldersModel.clear();
        for(var i = 0; i < items.length; ++i) {
            foldersModel.append(items[i]);
        }
    }

    MouseArea {
        id: mainMouseArea
        anchors.fill: parent
        propagateComposedEvents: true
        onClicked: {
            topBar.forceActiveFocus();
        }
    }

    Rectangle {
        id: topBar
        height: 40
        color: theme.background
        anchors.top: parent.top
        anchors.topMargin: 0
        anchors.left: parent.left
        anchors.leftMargin: 0
        anchors.right: parent.right
        anchors.rightMargin: 0


        RowLayout {
            anchors.rightMargin: 5
            anchors.leftMargin: 5
            spacing: 2
            anchors.fill: parent

            Text {
                id: titleText
                height: 28
                color: theme.foreground
                text: qsTr("Fukurou Downloader")
                font.family: "Verdana"
                font.pointSize: 17
                verticalAlignment: Text.AlignVCenter
            }

            TextIconButton {
                id: createFavFolder
                Layout.alignment: Qt.AlignRight | Qt.AlignVCenter
                ToolTip.visible: this.mouseArea.containsMouse
                ToolTip.text: qsTr("Add new folder")
                fontFamily: fontAwesome.name
                buttonText: "\uf067"
                verticalOffset: 1
                mouseArea.onClicked: {
                    forceActiveFocus();
                    folderPopup.visible = true;
                }
            }

            TextIconButton {
                id: openHistoryButton
                Layout.alignment: Qt.AlignRight | Qt.AlignVCenter
                ToolTip.visible: this.mouseArea.containsMouse
                ToolTip.text: qsTr("Open history page")
                fontFamily: fontAwesome.name
                buttonText: "\uf1da"
                mouseArea.onClicked: {
                    forceActiveFocus();
                    console.log("opening settings");
                }
            }

            TextIconButton {
                id: openSettingsButton
                Layout.alignment: Qt.AlignRight | Qt.AlignVCenter
                ToolTip.visible: this.mouseArea.containsMouse
                ToolTip.text: qsTr("Open settings page")
                fontFamily: fontAwesome.name
                buttonText: "\uf013"
                mouseArea.onClicked: {
                    forceActiveFocus();
                    console.log("opening settings");
                }
            }
        }
    }

    FolderPopup {
        id: folderPopup
        visible: false
    }


    TabView {
        id: tabs
        anchors.topMargin: 0
        anchors.top: topBar.bottom
        anchors.right: parent.right
        anchors.bottom: parent.bottom
        anchors.left: parent.left


        Tab {
            title: "History"
            ScrollView {
                ListView {
                    id: historyView
                    anchors.fill: parent
                    model: historyModel
                    interactive: true
                    //enabled: false
                    delegate: HistoryItem{}
                    section.property: "date"
                    section.criteria: ViewSection.FullString
                    section.delegate: sectionHeading
                    spacing: 8
                    snapMode: ListView.NoSnap
                    footer: seeMoreButton
                    clip: true
                }
            }
        }
        Tab {
            id: foldersTab
            title: "Folders"

            ScrollView {
                anchors.fill: parent
                ListView {
                    id: folderView

                    model: foldersModel
                    delegate: FolderItem {}


                }
            }
        }
    }

    Component {
        id: sectionHeading
        Rectangle {
            width: parent.width
            height: 30
            color: "lightsteelblue"

            Text {
                text: section
                font.bold: true
                font.pixelSize: 20
                anchors.verticalCenter: parent.verticalCenter
            }
        }
    }

    ListModel {
        id: historyModel
    }
    ListModel {
        id: foldersModel
    }

    Component {
        id: seeMoreButton
        Rectangle {
            height: 50
            anchors.right: parent.right
            anchors.rightMargin: 15
            anchors.left: parent.left
            anchors.leftMargin: 0
            Text {
                anchors.verticalCenter: parent.verticalCenter
                anchors.horizontalCenter: parent.horizontalCenter
                font.underline: true
                text: qsTr("SEE MORE")
            }
        }
    }
}
