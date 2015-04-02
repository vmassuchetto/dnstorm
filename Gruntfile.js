module.exports = function(grunt) {

    grunt.initConfig({
        jshint: {
            files: ['Gruntfile.js', 'dnstorm/app/static/js/scripts.js'],
            options: {
                globals: {
                    jQuery: true
                }
            }
        },
        sass: {
            options: {
                includePaths: ['dnstorm/app/static/components']
            },
            compile: {
                files: {
                    'dnstorm/app/static/css/app.css': 'dnstorm/app/static/scss/app.scss'
                }
            }
        },
        watch: {
            jshint: {
                files: ['dnstorm/app/static/js/scripts.js'],
                tasks: ['jshint']
            },
            sass: {
                files: [
                    'dnstorm/app/static/scss/app.scss',
                    'dnstorm/app/static/scss/_settings.scss'
                ],
                tasks: ['sass']
            }
        }
    });

    grunt.loadNpmTasks('grunt-contrib-jshint');
    grunt.loadNpmTasks('grunt-contrib-watch');
    grunt.loadNpmTasks('grunt-sass');

    grunt.registerTask('build', ['sass', 'jshint']);
    grunt.registerTask('default', ['watch']);

};
