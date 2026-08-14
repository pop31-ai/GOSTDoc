// Класс главного окна приложения.
class MainWindow : public QMainWindow {
public:
    MainWindow();
    void openFile();
    void saveFile();
    void processImage();
private:
    QString currentFile;
    QImage image;
    QLabel* statusBarLabel;
};

// Класс обработки изображений.
class ImageProcessor {
public:
    ImageProcessor();
    QImage filter(const QImage& img);
    QImage resize(const QImage& img, int w, int h);
    QImage grayscale(const QImage& img);
private:
    int quality;
};
