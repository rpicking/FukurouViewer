import QtQuick 2.7
import QtQuick.Window 2.2
import QtQuick.Dialogs 1.2
import QtQuick.Controls 2.1

import QtQuick.Controls 1.4
import QtQuick.Controls.Styles 1.4

import QtQuick.Layouts 1.1
import Qt.labs.settings 1.0

import "."


ApplicationWindow {
    id: mainWindow
    width: 400
    height: 640
    title: "Fukurou Viewer"

    Settings {
        id: settings
        property alias x: mainWindow.x
        property alias y: mainWindow.y
        property alias width: mainWindow.width
        property alias height: mainWindow.height
    }


    signal requestHistory(int index, int limit)
    signal receiveHistory(var items)
    signal requestFolders
    signal receiveFolders(var items)
    signal createFavFolder(string name, string path, string color, int type)
    signal onWindowClose
    signal requestValidFolder(string path)
    signal receiveValidFolder(bool valid)
    signal deleteHistoryItem(int id, int count)
    signal updateFolders(var items)
    signal openItem(string path, string type)
    signal openUrl(string url)
    signal updateProgress(var progress, int speed)
    signal addDownloadItem(string uid, var info)
    signal downloader_task(string id, string task)
    signal resume_download(string id)
    signal remove_download_ui_item(string id, string status)


    function closeWindows() {
        hide();
        onWindowClose();
    }

    function openWindow(mode, geometry) {
        switch(mode) {
            case "TRAY":
                trayWindow.openWindow(geometry.x, geometry.y);
                //requestHistory();
                break;
            case "APP":
                show();
                break;
            default:
                console.log("NOT SUPPOSED TO BE HERE");
                console.log(mode);
                //popup.open();
        }
    }

    TrayWindow { id: trayWindow }

    // *********************************************
    // **** Main Window ****************************
    // *********************************************

    Component {
        id: gridDelegate
        Item {
            width: grid.cellWidth
            height: grid.cellHeight
            Image {
                width: 200
                height: 280
                fillMode: Image.PreserveAspectFit
                source: "file:///" + filepath
                anchors.centerIn: parent
            }
        }
    }

    Rectangle {
        id: topBar
        height: 64
        color: Styles.background
        anchors {
            left: parent.left
            top: parent.top
            right: parent.right
        }

        Text {
            id: title
            text: "Fukurou"
            font.pointSize: 18
            color: Styles.foreground
            anchors {
                left: parent.left
                leftMargin: 20
                verticalCenter: parent.verticalCenter
            }
        }
        Rectangle {
            id: searchRect
            x: 16
            y: 16
            height: 36
            color: "#ffffff"
            radius: 5
            border.width: 0
            anchors {
                left: title.right
                leftMargin: 20
                right: topBarButtons.left
                rightMargin: 6
                verticalCenter: parent.verticalCenter
            }

            Label {
                id: searchIcon
                color: Styles.primary
                font.family: Fonts.solidIcons
                font.pixelSize: 20
                text: "\uf002"
                anchors.verticalCenterOffset: 0
                anchors.verticalCenter: parent.verticalCenter
                anchors.leftMargin: 8
                anchors.left: parent.left

            }
            TextField {
                id: searchText
                placeholderText: "Search"
                font.pointSize: 14
                style: TextFieldStyle { background: Rectangle {} }
                anchors {
                    left: searchIcon.right
                    top: parent.top
                    topMargin: 1
                    right: clearSearch.left
                    bottom: parent.bottom
                    bottomMargin: 1
                }
            }
            TextIconButton {
                id: clearSearch
                text: "\uf00d"
                textColor: Styles.primary
                visible: searchText.text !== ""
                anchors {
                    verticalCenter: parent.verticalCenter
                    right: parent.right
                    rightMargin: 6
                }

                onClicked: {
                    searchText.text = "";
                }
            }
        }

        Row {
            id: topBarButtons
            spacing: 5
            anchors.verticalCenter: parent.verticalCenter
            layoutDirection: Qt.RightToLeft
            anchors {
                right: parent.right
                margins: 5
            }
        }
    }



    ScrollView {
        id: scrollView
        anchors {
            left: parent.left
            top: topBar.bottom
            right: parent.right
            bottom: parent.bottom
        }

        //anchors.fill: parent
        //anchors.centerIn: parent
        //width: parent.width
        //height: parent.height


        function encodeURIComponents(uri) {
            return uri.split('/').map(encodeURIComponent).join('/')
        }

        GridView {
            id: grid
            //width: parent.viewport.width
            //width: Math.floor(parent.width / cellWidth) * cellWidth
            //height: parent.viewport.height
            property int viewportWidth: parent.width //mainWindow.width - 20 // avoid binding loop with scrollview viewport
            property int columns: viewportWidth / 220
            cellWidth: Math.floor(viewportWidth / columns)//Math.floor(width / Math.floor(parent.width / 220))
            cellHeight: 300
            model: gridModel
            interactive: true
            boundsBehavior: Flickable.StopAtBounds
            cacheBuffer: (350 + 16) * 25

            anchors {
                left: parent.left
                top: parent.top
                bottom: parent.bottom
            }
            delegate: Component {
                Loader {
                    sourceComponent: Component {
                        Item {
                            width: grid.cellWidth
                            height: grid.cellHeight

                            BusyIndicator {
                                anchors.centerIn: parent
                                running: picture.status != Image.Ready
                            }

                            Image {
                                id: picture
                                width: 200
                                height: 280
                                sourceSize.width: width
                                sourceSize.height: height
                                //cache: true
                                asynchronous: true
                                //mipmap: true
                                fillMode: Image.PreserveAspectFit
                                source: "image://test/" + encodeURIComponent(filepath) //"file:///" + filepath //scrollView.encodeURIComponents(filepath)
                                anchors.centerIn: parent
                                smooth: false
                                onStateChanged: {
                                    if (status == Image.Ready) {
                                        smooth = true;
                                    }
                                }

                                states: [
                                    State { name: 'loaded'; when: picture.status == Image.Ready }
                                ]
                            }
                        }
                    }
                    asynchronous: index >= 60
                }
            }
        }
    }


    /*Popup {
        id: popup
        x: 100
        y: 100
        width: 200
        height: 300
        modal: true
        focus: true
        closePolicy: Popup.CloseOnEscape | Popup.CloseOnPressOutsideParent

        ColumnLayout {
            anchors.fill: parent
            CheckBox { text: qsTr("E-mail") }
            CheckBox { text: qsTr("Calendar") }
            CheckBox { text: qsTr("Contacts") }
        }
    }

    FileDialog {
        id: fileDialog
        title: "Please choose a file"
        folder: shortcuts.home
        selectFolder: true
        selectMultiple: false
        onAccepted: {
            var path = fileDialog.fileUrl.toString();
            // remove prefixed "file:///"
            path = path.replace(/^(file:\/{3})/,"");
            // unescape html codes like '%23' for '#'
            var cleanPath = decodeURIComponent(path);
            console.log(cleanPath)
            Qt.quit()
        }
        onRejected: {
            console.log("Canceled")
            Qt.quit()
        }
        //Component.onCompleted: visible = true
    }*/
}
