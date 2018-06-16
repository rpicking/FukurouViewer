import QtQuick 2.0
import QtQuick.Window 2.2
import QtQuick.Dialogs 1.2
import QtQuick.Layouts 1.1
import QtQuick.Controls 2.1
import QtQuick.Controls 1.4
import QtQuick.Controls.Styles 1.4

import "controls" as Awesome

Window {
    id: trayWindow
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
        requestHistory(0);
        mainWindow.requestFolders();
        //console.log(active);
    }

    function closeWindow() {
        topBar.forceActiveFocus();
        hide();
    }

    function requestHistory(index) {
        var count = 50;
        mainWindow.requestHistory(index, count);   //0 = get all history
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

    function deleteHistoryItem(id, index) {
        historyModel.remove(index);
        topBar.forceActiveFocus();
        mainWindow.deleteHistoryItem(id, historyModel.count);
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
                ToolTip.visible: hovered
                ToolTip.text: qsTr("Add new folder")
                text: "\uf067"
                verticalOffset: 1
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

        style: TabViewStyle {
            frameOverlap: 0
            tab: Rectangle {
                color: styleData.selected ? theme.background :"white"
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
                    model: historyModel
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
                            requestHistory(historyModel.count);
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
        id: historyModel
    }
    ListModel {
        id: foldersModel
    }
}
