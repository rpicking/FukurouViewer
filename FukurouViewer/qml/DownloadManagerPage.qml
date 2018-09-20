import QtQuick 2.0

Item {
    property string tab: "default"

    Component.onCompleted: {
        console.log(tab);
    }

    Text {
        text: "Downloads Manager"
        fontSizeMode: Text.Fit
        minimumPixelSize: 12
        width: parent.width
        height: parent.height
        font.pointSize: 800
        verticalAlignment: Text.AlignVCenter
    }
}
