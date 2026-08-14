cmake_minimum_required(VERSION 3.16)
project(SampleApp VERSION 1.2.0 LANGUAGES CXX)

find_package(Qt6 REQUIRED COMPONENTS Widgets Network)

qt_add_executable(SampleApp
    mainwindow.h
    main.cpp
)

target_link_libraries(SampleApp PRIVATE Qt6::Widgets Qt6::Network)
