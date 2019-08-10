import QtQuick 2.11
import QtQuick.Window 2.2
import QtQuick.Dialogs 1.2
import QtQuick.Controls 2.1
import QtQuick.Layouts 1.1

import Qt.labs.settings 1.0

import "."


ApplicationWindow {
    id: mainWindow
    width: 1200
    height: 900
    title: "Fukurou Viewer"
    background: Rectangle {
        color: Styles.listBackground
    }


    Settings {
        id: settings
        property alias x: mainWindow.x
        property alias y: mainWindow.y
        property alias width: mainWindow.width
        property alias height: mainWindow.height
    }


    signal requestFolders
    signal receiveFolders(var items)
    signal createFavFolder(string name, string path, string color, int type)
    signal onWindowClose
    signal requestValidFolder(string path)
    signal receiveValidFolder(bool valid)
    signal updateFolders(var items)
    signal openItem(string path, string type)
    signal openUrl(string url)
    signal updateProgress(var progress, int speed)
    signal addDownloadItem(string uid, var info)
    signal downloader_task(string id, string task)
    signal resume_download(string id)
    signal setEventFilter(point coord, int thumb_width, int thumb_height, int item_width, int item_height, real xPercent, real yPercent)
    signal closeApplication
    signal scrollBlowUp(real scrollAmount)


    function openWindow(mode, geometry) {
        switch(mode) {
            case "TRAY":
                trayWindow.openWindow(geometry.x, geometry.y);
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

    function closeWindows() {
        hide();
        onWindowClose();
        closeBlowUpWindow();
    }

    function minimizeWindows() {
        showMinimized();
    }

    function closeBlowUpWindow() {
        testPopup.closeAndReset();
    }

    onActiveChanged: {
        if (mainWindow.active && trayWindow.visible) {
            trayWindow.hide();
        }
    }

    onClosing: {
        close.accepted = false;
        closeApplication();
    }

    TrayWindow { id: trayWindow }

    header: Rectangle {
        id: topBar
        height: 64
        color: Styles.background

        states: [
            State {
                name: "settings"
                PropertyChanges {
                    target: title
                    text: "Settings"
                }
            }
        ]

        Row {
            id: navigationButtons
            spacing: 5
            anchors {
                verticalCenter: parent.verticalCenter
                left: parent.left
                margins: 20
            }

            TextIconButton {
                id: backButton
                text: "\uf060"
                textColor: Styles.foreground
                height: 30
                visible: stack.depth > 1
                anchors.verticalCenter: parent.verticalCenter
                onClicked: stack.pop();
            }

            Image {
                id: logo
                source: "../icon.png"
                height: 50
                width: height
            }

            Text {
                id: title
                text: "Fukurou"
                font.pointSize: 18
                color: Styles.foreground
                anchors.verticalCenter: parent.verticalCenter
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
                left: navigationButtons.right
                leftMargin: 20
                right: topBarButtons.left
                rightMargin: 5
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
                background: Rectangle {}
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
            spacing: 15
            anchors.verticalCenter: parent.verticalCenter
            padding: 15
            anchors {
                right: parent.right
                margins: 5
            }
			
            TextIconButton {
                id: sortButton
                text: "\uf0dc"
                textColor: Styles.foreground
                onClicked: sortPopup.open()
				
                Popup {
                    id: sortPopup
                    x: parent.x - width
                    y: sortButton.height
                    width: 200
                    //height: 300
                    modal: true
                    focus: true
                    closePolicy: Popup.CloseOnEscape | Popup.CloseOnPressOutsideParent

                    ColumnLayout {
                        anchors.fill: parent

                        ButtonGroup { id: sortType }
                        RadioButton { text: qsTr("Name"); ButtonGroup.group: sortType }
                        RadioButton { text: qsTr("Date Modified"); checked: true; ButtonGroup.group: sortType }
                        RadioButton { text: qsTr("Date Added"); ButtonGroup.group: sortType }
                        RadioButton { text: qsTr("Last Read"); ButtonGroup.group: sortType }
                        RadioButton { text: qsTr("Read Count"); ButtonGroup.group: sortType }
                        RadioButton { text: qsTr("Rating"); ButtonGroup.group: sortType }

                        MenuSeparator {}

                        // GROUP BY
                        ButtonGroup { id: sortGroup }
                        RadioButton { text: qsTr("None"); checked: true; ButtonGroup.group: sortGroup }
                        RadioButton { text: qsTr("Artist"); ButtonGroup.group: sortGroup }
                        RadioButton { text: qsTr("Group"); ButtonGroup.group: sortGroup }

                        MenuSeparator {}

                        ButtonGroup { id: sortDirection }
                        RadioButton { text: qsTr("Ascending"); ButtonGroup.group: sortDirection }
                        RadioButton { text: qsTr("Descending"); checked: true; ButtonGroup.group: sortDirection }

                    }
                }
            }
			
            TextIconButton {
                id: menuButton
                text: "\uf0c9"
                textColor: Styles.foreground
                onClicked: menu.open()
				
                Menu {
                    id: menu
                    y: menuButton.height
                    background: Rectangle {
                        implicitWidth: 200
                        implicitHeight: 200
                        color: "#ffffff"
                    }

                    MenuItem {
                        text: "Download Manager"

                        onTriggered: stack.push(Qt.resolvedUrl("DownloadManagerPage.qml"))
                    }
                    MenuItem {
                        text: "History"
                        onTriggered: stack.push(Qt.resolvedUrl("DownloadManagerPage.qml"), { tab: "history" })
                    }

                    MenuItem {
                        text: "Folders"
                        onTriggered: stack.push(Qt.resolvedUrl("SettingsPage.qml"), { tab: "folders" } )
                    }


                    MenuItem {
                        text: "Fetch Metadata"
                        onTriggered: console.log("metadata")
                    }

                    MenuItem {
                        text: "Check Duplicates"
                        onTriggered: stack.push(Qt.resolvedUrl("DuplicatesPage.qml"))
                    }

                    MenuItem {
                        text: "Settings"
                        onTriggered: stack.push(Qt.resolvedUrl("SettingsPage.qml"))
                    }
                }
            }
        }
    }

    StackView {
        id: stack
        anchors.fill: parent
        initialItem: galleryView
    }

    MouseArea {
        id: mainMouseArea
        acceptedButtons: Qt.BackButton
        propagateComposedEvents: true
        anchors {
           top: mainWindow.header.top
           bottom: mainWindow.bottom
           left: mainWindow.left
           right: mainWindow.right
        }

        onClicked: {
            switch(mouse.button) {
            case Qt.BackButton:
                stack.pop();
                break;
            }
        }
    }

    GalleryView {
        id: galleryView
    }


    // *********************************************
    // ****** Mouse Hold Blow Up *******************
    // *********************************************

    Window {
        id: testPopup
        width: blowUpContent.loaderItem.width
        height: blowUpContent.loaderItem.height
        flags: Qt.FramelessWindowHint
        x: blowUp.x
        y: blowUp.y

        function openOnPoint(globalCoords, thumb_width, thumb_height, xPercent, yPercent) {
            setEventFilter(globalCoords, thumb_width, thumb_height, width, height, xPercent, yPercent);
        }

        function setSource(file) {
            blowUpContentLoader.sourceComponent = imageComponent
            blowUpContent.loaderItem.source = file
        
        }

        function closeAndReset() {
            blowUpContent.height = undefined;
            blowUpContent.width = undefined;
            hide();
        }

        Item {
            id: blowUpContent
            property alias loaderItem: blowUpContentLoader.item

            Loader {
                id: blowUpContentLoader
                sourceComponent: imageComponent //(logo) ? "TeamLogoItem.qml" : "TeamItem.qml"
            }
        }

        Component {
            id: imageComponent
            BlowUpImage { }
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
