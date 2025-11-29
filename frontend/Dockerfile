# Tomcat 9.0과 Java 11을 기반으로 하는 경량 이미지를 사용합니다.
FROM tomcat:9.0-jdk11-openjdk-slim

# 기존 ROOT 애플리케이션을 삭제합니다.
RUN rm -rf /usr/local/tomcat/webapps/ROOT

# JSP 파일을 웹 애플리케이션 루트로 복사합니다.
COPY ./webapp /usr/local/tomcat/webapps/ROOT
