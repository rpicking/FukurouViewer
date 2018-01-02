import QtQuick 2.7
import QtQuick.Window 2.2
import QtQuick.Dialogs 1.2
import QtQuick.Controls 2.1
//import QtQuick.Controls.Material 2.1
import QtQuick.Layouts 1.1
import Qt.labs.settings 1.0


ApplicationWindow {
    id: mainWindow
    width: 400
    height: 640
    title: "Fukurou Viewer"

    //theme colors
    QtObject {
        id: theme
        property string primary: "#393D3F"
        property string accent: "#9B1D20"
        property string foreground: "#FFFFFF"
        property string background: "#272727"
        property string highlighted: "#AD4648"
    }

    Settings {
        property alias x: mainWindow.x
        property alias y: mainWindow.y
        property alias width: mainWindow.width
        property alias height: mainWindow.height
    }

    property string mode: "NONE"

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

    function closeWindows() {
        hide();
        onWindowClose();
    }

    function openWindow(geometry) {
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
                popup.open();
        }
    }

    function setMode(_mode) {
        mode = _mode;
    }

    FontLoader {
        id: fontAwesome
        source: "fonts/fontawesome.4.7.webfont.ttf"
    }

    TrayWindow {
        id: trayWindow
    }

    Popup {
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



    MouseArea {
        anchors.fill: parent
        onClicked: {
            console.log(qsTr('Clicked on background. Text: "' + textEdit.text + '"'))
        }
    }

    Column {
        anchors.centerIn: parent

        RadioButton { text: qsTr("Small") }
        RadioButton { text: qsTr("Medium");  checked: true }
        RadioButton { text: qsTr("Large") }
    }


    /*FileDialog {
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
