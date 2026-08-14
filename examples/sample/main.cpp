#include "mainwindow.h"
#include <QFileDialog>

void MainWindow::openFile() {
    QString path = QFileDialog::getOpenFileName();
    if (!path.isEmpty()) {
        image.load(path);
        statusBarLabel->setText(path);
    }
}

void MainWindow::saveFile() {
    QString path = QFileDialog::getSaveFileName();
    if (!path.isEmpty()) {
        image.save(path);
    }
}

void MainWindow::processImage() {
    ImageProcessor p;
    image = p.grayscale(image);
    image = p.resize(image, 800, 600);
    update();
    connect(this, &MainWindow::imageProcessed, this, &MainWindow::updateStatus);
    emit imageProcessed(currentFile);
}

int main(int argc, char* argv[]) {
    QApplication app(argc, argv);
    MainWindow w;
    w.show();
    return app.exec();
}
