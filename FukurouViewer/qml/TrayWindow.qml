import QtQuick 2.11
import QtQuick.Window 2.2
import QtQuick.Dialogs 1.2
import QtQuick.Layouts 1.1
import QtQuick.Controls 2.1
import QtQuick.Controls 1.4
import QtQuick.Controls.Styles 1.4

import "."

Window {
    id: trayWindow
    //visible: false
    flags: Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Popup
    width: 400
    height: 640

    Component.onCompleted: {
        mainWindow.receiveFolders.connect(setFolders);
        mainWindow.onWindowClose.connect(closeWindow);
    }

    onActiveChanged: {
        if(!active && !folderPopup.visible) {
            closeWindow();
        }
    }

    function openWindow(_x, _y) {
        x = _x - width;
        y = _y - height;
        show();
        requestActivate();
        mainWindow.requestFolders();
    }

    function closeWindow() {
        topBar.forceActiveFocus();
        hide();
    }

    function setHistory(items) {
        //historyModel.clear();

        var tD = new Date();
        var today = getDateFormat(tD);

        var yD = new Date(today);
        yD.setDate(tD.getDate() - 1);
        var yesterday = getDateFormat(yD);

        for(var i = 0; i < items.length; ++i) {
            var d = new Date(items[i].time_added * 1000);
            var date = getDateFormat(d);
            if (date === today) {
                date = "Today";
            }
            else if (date === yesterday) {
                date = "Yesterday";
            }

            items[i]["date"] = date;
            historyModel.append(items[i]);
        }
    }

    function getDateFormat(date) {
        const monthNames = [
                    "January", "February", "March",
                    "April", "May", "June", "July",
                    "August", "September", "October",
                    "November", "December"
                ];

        var month = monthNames[date.getMonth()];
        var day = date.getDate();
        var year = date.getFullYear();

        return month + ' ' + day + ', ' + year;
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
            //topBar.forceActiveFocus();
        }
    }

    Rectangle {
        id: topBar
        height: 40
        color: Styles.background

        anchors {
            top: parent.top
            left: parent.left
            right: parent.right
        }

        Text {
            id: titleText
            height: 28
            color: Styles.foreground
            text: "Fukurou"
            anchors.verticalCenter: parent.verticalCenter
            font.family: "Verdana"
            font.pointSize: 17
            verticalAlignment: Text.AlignVCenter
            anchors {
                left: parent.left
                margins: 5
            }
        }

        Row {
            id: row
            spacing: 5
            anchors.verticalCenter: parent.verticalCenter
            anchors {
                right: parent.right
                margins: 5
            }

            TextIconButton {
                id: createFavFolder
                Layout.alignment: Qt.AlignRight | Qt.AlignVCenter
                ToolTip.visible: hovered
                ToolTip.text: qsTr("Add new folder")
                text: "\uf067"
                //verticalOffset: 1
                onClicked: {
                    forceActiveFocus();
                    folderPopup.visible = true;
                }
            }
            TextIconButton {
                id: openHistoryButton
                Layout.alignment: Qt.AlignRight | Qt.AlignVCenter
                ToolTip.visible: hovered
                ToolTip.text: qsTr("Open history page")
                text: "\uf1da"
                onClicked: {
                    forceActiveFocus();
                    console.log("opening history");
                }
            }
            TextIconButton {
                id: openSettingsButton
                Layout.alignment: Qt.AlignRight | Qt.AlignVCenter
                ToolTip.visible: hovered
                ToolTip.text: qsTr("Open settings page")
                text: "\uf013"
                onClicked: {
                    mainWindow.show();
                    closeWindow();
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

        style: TabViewStyle {
            frameOverlap: 0
            tab: Rectangle {
                color: styleData.selected ? Styles.background :"white"
                //border.color:  "transparent"
                implicitWidth: Math.max(tabTitle.width + 8, 80)
                implicitHeight: 20
                //radius: 2
                Text {
                    id: tabTitle
                    anchors.centerIn: parent
                    text: styleData.title
                    color: styleData.selected ? "white" : "black"
                }
            }
        }

        Tab {
            id: downloadsTab
            title: "Downloads"

            PopupDownloadsTab {}
        }

        Tab {
            id: historyTab
            title: "History"

            ScrollView {
                ListView {
                    id: historyView
                    anchors.fill: parent
                    model: history.model
                    interactive: true
                    //enabled: false
                    delegate: HistoryItem{}
                    section.property: "date"
                    section.criteria: ViewSection.FullString
                    section.delegate: sectionHeading
                    spacing: 6
                    snapMode: ListView.NoSnap
                    clip: true
                    cacheBuffer: 0

                    onAtYEndChanged: {
                        if (atYEnd) {
                            history.load_existing();
                        }
                    }
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
        id: foldersModel
    }
}
