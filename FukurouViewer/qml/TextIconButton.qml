import QtQuick 2.0
import QtQuick.Controls 2.1

Button {
    id: root
    property string textColor : hovered ? theme.highlighted : theme.accent
    property string backgroundColor : "transparent"
    property string borderColor: "transparent"
    property int verticalOffset : 0
    property int horizontalOffset : 0

    height: 25
    width: height

    padding: 0
    font: fontAwesome.name
    baselineOffset: 0

    contentItem: Text {
        font.family: root.font
        font.pixelSize: root.height
        color: textColor
        text: root.text
        fontSizeMode: Text.Fit
        //minimumPointSize: root.height
        horizontalAlignment: Text.AlignHCenter
        verticalAlignment: Text.AlignVCenter
        anchors {
            horizontalCenter: root.horizontalCenter
            horizontalCenterOffset: horizontalOffset
            verticalCenter: root.verticalCenter
            verticalCenterOffset: verticalOffset
        }
    }

    background: Rectangle {
        border.color: borderColor
        color: backgroundColor
        implicitHeight: root.height
        implicitWidth: root.height
    }
}
